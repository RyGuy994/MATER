// filepath: MATER/MATER_FE/src/components/settings/UserSettings.jsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "../../utils/api";
import "../login/Login.css";
import "./UserSettings.css";

const THEME_STORAGE_KEY = "mater_theme"; // saved preference

const THEME_OPTIONS = [
  { value: "default", label: "Default" }, // removes data-theme
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "custom", label: "Custom" },
];

function applyTheme(themeValue) {
  const root = document.documentElement; // <html> [web:308]
  if (themeValue === "default") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", themeValue);
  }
}

export default function UserSettings() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [me, setMe] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Theme state
  const initialTheme = useMemo(() => {
    return localStorage.getItem(THEME_STORAGE_KEY) || "system";
  }, []);
  const [theme, setTheme] = useState(initialTheme);

  // Profile fields
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  // Password fields
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");

  // MFA placeholders
  const [mfaEnabled, setMfaEnabled] = useState(false);

  // Apply theme on mount + whenever it changes
  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme); // persists across sessions [web:83]
  }, [theme]);

  useEffect(() => {
    const token = localStorage.getItem("mater_token");
    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await apiGet("/auth/me");
        const user = data?.user || data;

        setMe(user);
        setUsername(user?.username || "");
        setEmail(user?.email || "");

        setMfaEnabled(Boolean(user?.mfa_enabled));
      } catch (e) {
        setError(e.message || "Failed to load user settings.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [navigate]);

  const clearAlerts = () => {
    setError("");
    setMessage("");
  };

  const handleLogout = () => {
    // If you also set an auth cookie server-side, you can optionally call /auth/logout too.
    localStorage.removeItem("mater_token");
    setMe(null);
    navigate("/login", { replace: true });
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    clearAlerts();
    setSaving(true);

    try {
      // NOTE: your backend currently has these under /auth/users/me in the example earlier.
      // If your backend kept /users/me (no /auth prefix), leave as-is.
      const data = await apiPost("/users/me", { username, email });
      setMessage(data?.message || "Profile updated.");
      const refreshed = await apiGet("/auth/me");
      setMe(refreshed?.user || refreshed);
    } catch (e2) {
      setError(e2.message || "Profile update failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    clearAlerts();

    if (!currentPassword || !newPassword) {
      setError("Current password and new password are required.");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setError("New passwords do not match.");
      return;
    }

    setSaving(true);
    try {
      const data = await apiPost("/users/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage(data?.message || "Password changed.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (e2) {
      setError(e2.message || "Password change failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleLinkSSO = async (provider) => {
    clearAlerts();

    if (provider === "google") {
      setMessage("Placeholder: Google linking will be implemented here.");
      return;
    }
    if (provider === "microsoft") {
      setMessage("Placeholder: Microsoft linking will be implemented here.");
      return;
    }
    if (provider === "apple") {
      setMessage("Placeholder: Apple linking will be implemented here.");
      return;
    }
  };

  const handleToggleMFA = async () => {
    clearAlerts();
    setSaving(true);

    try {
      await apiPost("/mfa/toggle", { enabled: !mfaEnabled });
      setMfaEnabled((v) => !v);
      setMessage("Placeholder: MFA change saved (implement backend).");
    } catch (e) {
      setError(e.message || "Failed to update MFA setting.");
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
      <div className="login-card settings-card">
        <h2>User Settings</h2>

        {me && (
          <p className="settings-muted">
            Signed in as {me.username || me.email}
          </p>
        )}

        {error && <p className="error-message">{error}</p>}
        {message && <p className="settings-success">{message}</p>}

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

        {/* SSO linking (placeholder) */}
        <section className="settings-section">
          <h3 className="settings-h3">Linked sign-in (SSO)</h3>

          <div className="settings-grid">
            <button
              type="button"
              className="create-account-button sso-btn sso-google"
              onClick={() => handleLinkSSO("google")}
              disabled={saving}
            >
              Link Google
            </button>

            <button
              type="button"
              className="create-account-button sso-btn sso-microsoft"
              onClick={() => handleLinkSSO("microsoft")}
              disabled={saving}
            >
              Link Microsoft
            </button>

            <button
              type="button"
              className="create-account-button sso-btn sso-apple"
              onClick={() => handleLinkSSO("apple")}
              disabled={saving}
            >
              Link Apple
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
