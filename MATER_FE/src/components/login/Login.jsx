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
        const accessToken = tokenResponse?.access_token;
        if (!accessToken) {
          setError("Google login failed");
          return;
        }

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

        {/* SSO Buttons - Updated structure */}
        <div className="sso-container">
          <button
            type="button"
            onClick={() => googleLogin()}
            disabled={loading}
            className="sso-button google-button"
          >
            <svg className="google-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span className="button-text">Sign in with Google</span>
          </button>

          <button
            type="button"
            onClick={handleAppleLogin}
            disabled={loading}
            className="sso-button apple-button"
          >
            <svg className="apple-icon" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.3-3.14-2.53C4.25 17.12 3.5 15.17 3.5 13.2c0-1.62.56-3.14 1.67-4.04.92-.74 2.44-1.58 3.74-1.58.95 0 1.7.6 2.5.6.7 0 1.8-.87 3.39-.72 1.61.08 2.42.66 3.04 1.56-.02.03-2.41 1.68-2.41 5c0 3.02 2.18 4.05 2.2 4.05-.04.06-.34 1.25-1.12 2.51z"/>
              <path d="M12.45 6.51c-.66-.73-1.79-1.23-2.65-1.23-.13 2.15 1.53 3.76 2.65 4.81.92-.88 1.38-2.37 1.38-3.36-.59-.3-1.23-.64-1.38-1.22z"/>
            </svg>
            <span className="button-text">Sign in with Apple</span>
          </button>

          <button
            type="button"
            onClick={handleEntraLogin}
            disabled={loading}
            className="sso-button microsoft-button"
          >
            <svg className="microsoft-icon" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="10" height="10" fill="#F25022"/>
              <rect x="12" width="11" height="10" fill="#7FBA00"/>
              <rect y="12" width="10" height="11" fill="#0078D4"/>
              <rect x="12" y="12" width="11" height="11" fill="#FFB900"/>
            </svg>
            <span className="button-text">Sign in with Microsoft</span>
          </button>
        </div>
      </div>
    </div>
  );
}
