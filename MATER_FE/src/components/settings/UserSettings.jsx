// filepath: MATER/MATER_FE/src/components/settings/UserSettings.jsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "../../utils/api";
import { useToast } from "../../hooks/useToast";
import Toast from "../toast/Toast";
import CustomTheme from "./CustomTheme";
import "../login/Login.css";
import "./UserSettings.css";


const THEME_STORAGE_KEY = "mater_theme";


const THEME_OPTIONS = [
  { value: "default", label: "Default" },
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "custom", label: "Custom" },
];


function applyTheme(themeValue) {
  const root = document.documentElement;
  if (themeValue === "default") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", themeValue);
  }
}


export default function UserSettings() {
  const navigate = useNavigate();
  const { toasts, showToast, dismissToast } = useToast();


  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);


  const [me, setMe] = useState(null);


  const initialTheme = useMemo(() => {
    return localStorage.getItem(THEME_STORAGE_KEY) || "system";
  }, []);
  const [theme, setTheme] = useState(initialTheme);


  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");


  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");


  const [mfaEnabled, setMfaEnabled] = useState(false);


  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);


  useEffect(() => {
    const token = localStorage.getItem("mater_token");
    if (!token) {
      navigate("/login", { replace: true });
      return;
    }


    const load = async () => {
      setLoading(true);
      try {
        const data = await apiGet("/auth/me");
        const user = data?.user || data;


        setMe(user);
        setUsername(user?.username || "");
        setEmail(user?.email || "");
        setMfaEnabled(Boolean(user?.mfa_enabled));
      } catch (e) {
        showToast(e.message || "Failed to load user settings.", "error");
      } finally {
        setLoading(false);
      }
    };


    load();
  }, [navigate, showToast]);


  const handleLogout = () => {
    localStorage.removeItem("mater_token");
    setMe(null);
    navigate("/login", { replace: true });
  };


  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);


    try {
      const data = await apiPost("/auth/users/me", { username, email });
      showToast(data?.message || "Profile updated.", "success");
      const refreshed = await apiGet("/auth/me");
      setMe(refreshed?.user || refreshed);
    } catch (e2) {
      showToast(e2.message || "Profile update failed.", "error");
    } finally {
      setSaving(false);
    }
  };


  const handleChangePassword = async (e) => {
    e.preventDefault();


    if (!currentPassword || !newPassword) {
      showToast("Current password and new password are required.", "error");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      showToast("New passwords do not match.", "error");
      return;
    }


    setSaving(true);
    try {
      const data = await apiPost("/auth/users/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      showToast(data?.message || "Password changed.", "success");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (e2) {
      showToast(e2.message || "Password change failed.", "error");
    } finally {
      setSaving(false);
    }
  };


  const handleLinkSSO = async (provider) => {
    if (provider === "google") {
      showToast("Placeholder: Google linking will be implemented here.", "info");
      return;
    }
    if (provider === "microsoft") {
      showToast("Placeholder: Microsoft linking will be implemented here.", "info");
      return;
    }
    if (provider === "apple") {
      showToast("Placeholder: Apple linking will be implemented here.", "info");
      return;
    }
  };


  const handleToggleMFA = async () => {
    setSaving(true);


    try {
      await apiPost("/mfa/toggle", { enabled: !mfaEnabled });
      setMfaEnabled((v) => !v);
      showToast("Placeholder: MFA change saved (implement backend).", "info");
    } catch (e) {
      showToast(e.message || "Failed to update MFA setting.", "error");
    } finally {
      setSaving(false);
    }
  };


  if (loading) {
    return (
      <div className="login-card settings-card">
        <h2>User Settings</h2>
        <p>Loading...</p>
      </div>
    );
  }


  return (
    <div className="settings-wrap">
      <div className="toast-container">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            duration={toast.duration}
            onDismiss={() => dismissToast(toast.id)}
          />
        ))}
      </div>


      <div className="login-card settings-card">
        <h2>User Settings</h2>


        {me && (
          <p className="settings-muted">
            Signed in as {me.username || me.email}
          </p>
        )}


        {/* Theme */}
        <section className="settings-section">
          <h3 className="settings-h3">Theme</h3>


          <div className="settings-label">Color theme</div>


          <div className="theme-picker">
            {THEME_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`theme-pill ${theme === opt.value ? "is-active" : ""}`}
                onClick={() => setTheme(opt.value)}
                disabled={saving}
              >
                {opt.label}
              </button>
            ))}
          </div>


          <p className="settings-muted">
            Saved on this device and applied next time you open MATER.
          </p>


          {/* Custom Theme Color Picker */}
          <CustomTheme isActive={theme === "custom"} />
        </section>


        {/* Profile */}
        <section className="settings-section">
          <h3 className="settings-h3">Profile</h3>


          <form onSubmit={handleSaveProfile} className="login-form">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="login-input"
            />
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="login-input"
            />


            <button type="submit" disabled={saving} className="login-button">
              {saving ? "Saving..." : "Save profile"}
            </button>
          </form>
        </section>


        {/* Password */}
        <section className="settings-section">
          <h3 className="settings-h3">Password</h3>


          <form onSubmit={handleChangePassword} className="login-form">
            <input
              type="password"
              placeholder="Current password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="login-input"
            />
            <input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="login-input"
            />
            <input
              type="password"
              placeholder="Confirm new password"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              className="login-input"
            />


            <button type="submit" disabled={saving} className="login-button">
              {saving ? "Saving..." : "Change password"}
            </button>
          </form>
        </section>


        {/* SSO linking - UPDATED WITH POLISHED BUTTONS */}
        <section className="settings-section">
          <h3 className="settings-h3">Linked sign-in (SSO)</h3>


          <div className="sso-container">
            <button
              type="button"
              onClick={() => handleLinkSSO("google")}
              disabled={saving}
              className="sso-button google-button"
            >
              <svg className="google-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              <span className="button-text">Link Google</span>
            </button>


            <button
              type="button"
              onClick={() => handleLinkSSO("apple")}
              disabled={saving}
              className="sso-button apple-button"
            >
              <svg className="apple-icon" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.3-3.14-2.53C4.25 17.12 3.5 15.17 3.5 13.2c0-1.62.56-3.14 1.67-4.04.92-.74 2.44-1.58 3.74-1.58.95 0 1.7.6 2.5.6.7 0 1.8-.87 3.39-.72 1.61.08 2.42.66 3.04 1.56-.02.03-2.41 1.68-2.41 5c0 3.02 2.18 4.05 2.2 4.05-.04.06-.34 1.25-1.12 2.51z"/>
                <path d="M12.45 6.51c-.66-.73-1.79-1.23-2.65-1.23-.13 2.15 1.53 3.76 2.65 4.81.92-.88 1.38-2.37 1.38-3.36-.59-.3-1.23-.64-1.38-1.22z"/>
              </svg>
              <span className="button-text">Link Apple</span>
            </button>


            <button
              type="button"
              onClick={() => handleLinkSSO("microsoft")}
              disabled={saving}
              className="sso-button microsoft-button"
            >
              <svg className="microsoft-icon" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="10" height="10" fill="#F25022"/>
                <rect x="12" width="11" height="10" fill="#7FBA00"/>
                <rect y="12" width="10" height="11" fill="#0078D4"/>
                <rect x="12" y="12" width="11" height="11" fill="#FFB900"/>
              </svg>
              <span className="button-text">Link Microsoft</span>
            </button>
          </div>


          <p className="settings-muted">
            Placeholders for now—wire these to your OAuth flows and store the linked provider IDs.
          </p>
        </section>


        {/* MFA (placeholder) */}
        <section className="settings-section">
          <h3 className="settings-h3">Multi-factor authentication (MFA)</h3>


          <div className="settings-row">
            <div>
              <div className="settings-label">MFA status</div>
              <div className="settings-muted">
                {mfaEnabled ? "Enabled" : "Disabled"} (placeholder)
              </div>
            </div>


            <button
              type="button"
              className="login-button"
              disabled={saving}
              onClick={handleToggleMFA}
            >
              {saving ? "Saving..." : mfaEnabled ? "Disable MFA" : "Enable MFA"}
            </button>
          </div>
        </section>


        {/* Logout (bottom) */}
        <div className="settings-footer">
          <button
            type="button"
            className="create-account-button settings-logout"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
