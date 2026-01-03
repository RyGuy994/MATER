// MATER_FE/src/pages/EntraCallback.jsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import jwt_decode from "jwt-decode"; // decode JWT to get username/email immediately

export default function EntraCallback() {
  const navigate = useNavigate();
  const backendUrl = import.meta.env.VITE_BACKEND_URL;

  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const code = query.get("code");

    if (!code) {
      navigate("/login", { replace: true });
      return;
    }

    const exchangeCode = async () => {
      try {
        const res = await fetch(`${backendUrl}/auth/entra/callback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code }),
        });

        if (!res.ok) {
          const error = await res.json().catch(() => ({ error: "Unknown error" }));
          console.error("Entra callback failed:", error);
          navigate("/login", { replace: true });
          return;
        }

        const data = await res.json();
        if (data.token) {
          // store token
          localStorage.setItem("mater_token", data.token);

          // optional: decode JWT to pass username/email immediately
          const payload = jwt_decode(data.token);
          const user = {
            username: payload.username || payload.email,
            email: payload.email,
          };

          // store in a global state if you have one, or just redirect
          console.log("Logged in user:", user);
        }

        // clean URL
        window.history.replaceState({}, document.title, window.location.pathname);

        navigate("/dashboard", { replace: true });
      } catch (err) {
        console.error("Error during Entra login:", err);
        navigate("/login", { replace: true });
      }
    };

    exchangeCode();
  }, [navigate, backendUrl]);

  return <p>Logging in with Entra...</p>;
}
