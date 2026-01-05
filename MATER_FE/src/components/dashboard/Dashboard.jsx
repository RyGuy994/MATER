// filepath: MATER/MATER_FE/src/components/dashboard/Dashboard.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../login/Login.css"; // to reuse .login-card styles

export default function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("mater_token");
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();
          setUserData(data.user);
        } else {
          localStorage.removeItem("mater_token");
          navigate("/login", { replace: true });
        }
      } catch (err) {
        console.error("Error fetching user data", err);
        navigate("/login", { replace: true });
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("mater_token");
    navigate("/login", { replace: true });
  };

  return (
    <div className="login-card" style={{ maxWidth: 800, margin: 0, textAlign: "left" }}>
      <h2>Dashboard</h2>

      {loading ? (
        <p>Loading user data...</p>
      ) : userData ? (
        <>
          <p>Welcome, {userData.username || userData.email}!</p>
          <button onClick={handleLogout} className="create-account-button">
            Logout
          </button>
        </>
      ) : (
        <p>You are not logged in.</p>
      )}
    </div>
  );
}
