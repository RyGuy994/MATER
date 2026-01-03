// filepath: MATER/MATER_FE/src/components/login/Login.jsx
import { useState } from "react";
import { useGoogleLogin } from "@react-oauth/google";
import { useNavigate } from "react-router-dom";
import { apiPost } from "../../utils/api";
import "./Login.css";

export default function Login({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ----------------------
  // Local login
  // ----------------------
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await apiPost("/auth/login", { email, password });

      if (data.mfa_required) {
        localStorage.setItem("mfa_user_id", data.user_id);
        navigate("/mfa");
        return;
      }

      if (data.token) localStorage.setItem("mater_token", data.token);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  // ----------------------
  // Generic SSO login helper
  // ----------------------
  const handleSSOLogin = async (provider, providerData) => {
    setError("");
    setLoading(true);

    try {
      const data = await apiPost("/auth/sso", { provider, ...providerData });

      if (data.mfa_required) {
        localStorage.setItem("mfa_user_id", data.user_id);
        navigate("/mfa");
        return;
      }

      if (data.token) localStorage.setItem("mater_token", data.token);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || `${provider} login failed`);
    } finally {
      setLoading(false);
    }
  };

  // ----------------------
  // Google SSO (custom button)
  // ----------------------
  const googleLogin = useGoogleLogin({
    flow: "implicit",
    scope: "openid profile email",
    onSuccess: async (tokenResponse) => {
      try {
        // tokenResponse has access_token with implicit flow. [web:419]
        const accessToken = tokenResponse?.access_token;
        if (!accessToken) {
          setError("Google login failed");
          return;
        }

        // Get the user's profile from Google using the access token.
        // This returns sub (Google user id), email, name, etc.
        const resp = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (!resp.ok) throw new Error("Failed to fetch Google profile");
        const profile = await resp.json();

        const provider_id = profile.sub;
        const email = profile.email;
        const username = profile.name || "";

        if (!provider_id || !email) throw new Error("Google profile missing required fields");

        await handleSSOLogin("google", { provider_id, email, username });
      } catch (e) {
        setError(e.message || "Google login failed");
        setLoading(false);
      }
    },
    onError: () => setError("Google login failed"),
  });

  // ----------------------
  // Apple SSO redirect
  // ----------------------
  const handleAppleLogin = () => {
    const clientId = import.meta.env.VITE_APPLE_CLIENT_ID;
    const redirectUri = import.meta.env.VITE_APPLE_REDIRECT_URI;
    const url =
      `https://appleid.apple.com/auth/authorize?response_type=code id_token` +
      `&client_id=${clientId}&redirect_uri=${redirectUri}` +
      `&scope=name email&state=randomString&response_mode=form_post`;
    window.location.href = url;
  };

  // ----------------------
  // Entra (Microsoft) SSO redirect
  // ----------------------
  const handleEntraLogin = () => {
    const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID;
    const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID;
    const redirectUri = import.meta.env.VITE_ENTRA_REDIRECT_URI;

    const url =
      `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize` +
      `?client_id=${clientId}` +
      `&response_type=code&redirect_uri=${redirectUri}` +
      `&scope=openid email profile&response_mode=query&state=randomString`;
    window.location.href = url;
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <img src="/MATER.png" alt="MATER" className="mater-logo" />
        <h2>Login to MATER</h2>
        {error && <p className="error-message">{error}</p>}

        {/* Local login */}
        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="login-input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
          />
          <button type="submit" disabled={loading} className="login-button">
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <button onClick={() => navigate("/register")} className="create-account-button">
          Create Account
        </button>

        <div className="divider">
          <span>OR</span>
        </div>

        {/* SSO Buttons (now matching your linking button styles) */}
        <div className="sso-container">
          <button
            type="button"
            onClick={() => googleLogin()}
            disabled={loading}
            className="create-account-button sso-btn sso-google"
          >
            <span className="button-text">Sign in with Google</span>
          </button>

          <button
            type="button"
            onClick={handleAppleLogin}
            disabled={loading}
            className="create-account-button sso-btn sso-apple"
          >
            <span className="button-text">Sign in with Apple</span>
          </button>

          <button
            type="button"
            onClick={handleEntraLogin}
            disabled={loading}
            className="create-account-button sso-btn sso-microsoft"
          >
            <span className="button-text">Sign in with Microsoft</span>
          </button>
        </div>
      </div>
    </div>
  );
}
