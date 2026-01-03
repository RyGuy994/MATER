// MATER/MATER_FE/src/components/register/Register.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiPost } from "../../utils/api";
import "../login/Login.css"; // reuse same styles

export default function Register() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Email and password are required.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiPost("/auth/register", { username, email, password });

      if (!data || !data.token) {
        setError(data?.error || "Registration failed");
        return;
      }

      localStorage.setItem("mater_token", data.token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Network error, please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <img src="/MATER.png" alt="MATER" className="mater-logo" />
        <h2>Create your MATER account</h2>

        {error && <p className="error-message">{error}</p>}

        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="text"
            placeholder="Username (optional)"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="login-input"
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
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
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="login-input"
          />
          <button type="submit" disabled={loading} className="login-button">
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        <button
          onClick={() => navigate("/login")}
          className="create-account-button"
        >
          Back to Login
        </button>
      </div>
    </div>
  );
}
