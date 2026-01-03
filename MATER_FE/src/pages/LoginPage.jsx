// MATER/MATER_FE/src/pages/LoginPage.jsx
import Login from "../components/login/Login";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const navigate = useNavigate();

  const handleLoginSuccess = () => {
    navigate("/dashboard", { replace: true });
  };

  return <Login onLoginSuccess={handleLoginSuccess} />;
}
