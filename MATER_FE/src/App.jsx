// MATER_FE/src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import EntraCallback from "./pages/EntraCallback";
import RegisterPage from "./pages/RegisterPage";
const backendUrl = import.meta.env.VITE_BACKEND_URL;

function App() {
  return (
    <Router>
      <Routes>
        {/* Login page */}
        <Route path="/login" element={<LoginPage />} />

        {/* Dashboard - protected route */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* Registration page */}
        <Route path="/register" element={<RegisterPage />} />

        {/* Default route */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* Entra OAuth callback */}
        <Route path="/entra-callback" element={<EntraCallback />} />
      </Routes>
    </Router>
  );
}

export default App;
