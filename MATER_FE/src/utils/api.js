// src/utils/api.js
const backendUrl = import.meta.env.VITE_BACKEND_URL;

async function request(endpoint, options = {}) {
  const token = localStorage.getItem("mater_token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  try {
    const res = await fetch(`${backendUrl}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.error || "Request failed");
    }

    return data;
  } catch (err) {
    console.error("API request error:", err);
    throw err;
  }
}

// Shortcut methods
export const apiGet = (endpoint) => request(endpoint, { method: "GET" });
export const apiPost = (endpoint, body) =>
  request(endpoint, { method: "POST", body: JSON.stringify(body) });
export const apiPut = (endpoint, body) =>
  request(endpoint, { method: "PUT", body: JSON.stringify(body) });
export const apiDelete = (endpoint) => request(endpoint, { method: "DELETE" });
