// src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

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
          headers: { "Authorization": `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setUserData(data.user);
        } else {
          // Invalid token → logout
          localStorage.removeItem("mater_token");
          setUserData(null);
          navigate("/login", { replace: true });
        }
      } catch (err) {
        console.error("Error fetching user data", err);
        setUserData(null);
        navigate("/login", { replace: true });
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("mater_token"); // clear token
    setUserData(null);
    navigate("/login", { replace: true }); // redirect to login
  };

  if (loading) {
    return (
      <div style={{ maxWidth: 600, margin: "50px auto", textAlign: "center" }}>
        <h1>Dashboard</h1>
        <p>Loading user data...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 600, margin: "50px auto", textAlign: "center" }}>
      <h1>Dashboard</h1>
      {userData ? (
        <>
          <p>Welcome, {userData.username || userData.email}!</p>
          <button onClick={handleLogout} style={{ marginTop: "1rem", padding: "8px 16px" }}>
            Logout
          </button>
        </>
      ) : (
        <p>You are not logged in.</p>
      )}
    </div>
  );
}
