// filepath: MATER/MATER_FE/src/pages/EntraCallback.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import jwt_decode from "jwt-decode";

export default function EntraCallback() {
  const navigate = useNavigate();
  const backendUrl = import.meta.env.VITE_BACKEND_URL;
  const [status, setStatus] = useState("Logging in with Entra...");

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const code = query.get("code");
    const state = query.get("state");
    const error = query.get("error");
    const errorDescription = query.get("error_description");

    // Entra can redirect back with an error instead of a code.
    if (error) {
      console.error("Entra error:", error, errorDescription);
      navigate("/login", {
        replace: true,
        state: { error: errorDescription || error },
      });
      return;
    }

    if (!code) {
      navigate("/login", { replace: true, state: { error: "Missing code in Entra callback URL" } });
      return;
    }

    // Validate state (CSRF protection). [web:22]
    const expectedState = sessionStorage.getItem("entra_oauth_state");
    if (!state) {
      navigate("/login", { replace: true, state: { error: "Missing state in Entra callback URL" } });
      return;
    }
    if (!expectedState || state !== expectedState) {
      navigate("/login", { replace: true, state: { error: "Invalid state. Please try again." } });
      return;
    }

    const exchangeCode = async () => {
      try {
        setStatus("Exchanging authorization code...");

        const res = await fetch(`${backendUrl}/auth/entra/callback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ code, state }),
        });

        const data = await res.json().catch(() => ({ error: "Unknown error" }));

        if (!res.ok) {
          console.error("Entra callback failed:", data);
          navigate("/login", { replace: true, state: { error: data?.error || "Entra login failed" } });
          return;
        }

        // Backend returns JSON token + also sets cookie
        if (data.token) {
          localStorage.setItem("mater_token", data.token);

          // jwt-decode is only for reading claims; it doesn't verify signatures. [web:78]
          try {
            const payload = jwt_decode(data.token);
            console.log("JWT payload:", payload);
          } catch {
            // ignore decode issues; token still stored
          }
        }

        // Prevent replay
        sessionStorage.removeItem("entra_oauth_state");
        sessionStorage.removeItem("entra_oauth_nonce");

        // Remove code/state from URL
        window.history.replaceState({}, document.title, window.location.pathname);

        navigate("/dashboard", { replace: true });
      } catch (err) {
        console.error("Error during Entra login:", err);
        navigate("/login", { replace: true, state: { error: "Network error during Entra login" } });
      }
    };

    exchangeCode();
  }, [navigate, backendUrl]);

  return <p>{status}</p>;
}
