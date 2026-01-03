// MATER/MATER_FE/src/components/login/Login.jsx
import { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useNavigate } from "react-router-dom";
import { apiPost } from "../../utils/api";
import './Login.css';

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
  // Google SSO
  // ----------------------
  const handleGoogleSuccess = async (credentialResponse) => {
    if (!credentialResponse?.credential) return setError("Google login failed");

    const base64Url = credentialResponse.credential.split(".")[1];
    const payload = JSON.parse(atob(base64Url));
    const { sub: provider_id, email, name } = payload;

    await handleSSOLogin("google", { provider_id, email, username: name || "" });
  };

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
  // Entra (Microsoft) SSO - BEAUTIFUL BUTTON ✨
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

      {/* SSO Buttons */}
      <div className="sso-container">
        <div className="google-wrapper">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={() => setError("Google login failed")}
            theme="filled_blue"
            size="large"
            shape="rectangular"
            text="signin_with"
            width="100%"
            logo_alignment="left"
            useOneTap={false}
          />
        </div>

        <button onClick={handleAppleLogin} disabled={loading} className="sso-button apple-button">
          <img 
            src="https://docs-assets.developer.apple.com/published/76a7de0f49ff86242e7a08f53ec57bb5/siwa-white-logo-only%402x.png" 
            alt="" 
            className="apple-icon"
          />
          <span className="button-text">Sign in with Apple</span>
        </button>

        <button onClick={handleEntraLogin} disabled={loading} className="sso-button microsoft-button">
          <svg className="microsoft-icon" viewBox="0 0 16 16" fill="currentColor">
            <path d="M7.462 0H0v7.19h7.462zM16 0H8.538v7.19H16zM7.462 8.211H0V16h7.462zm8.538 0H8.538V16H16z"/>
          </svg>
          <span className="button-text">Sign in with Microsoft</span>
        </button>
      </div>
    </div>
  </div>
);

}
