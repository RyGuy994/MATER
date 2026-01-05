// filepath: MATER_FE/src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import EntraCallback from "./pages/EntraCallback";
import SettingsPage from "./pages/SettingsPage";

import AppLayout from "./layouts/AppLayout";
import Dashboard from "./components/dashboard/Dashboard";

function App() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/entra-callback" element={<EntraCallback />} />

        {/* App routes (with sidebar) */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/settings" element={<SettingsPage />} />

          {/* Add these as you build the pages */}
          {/* <Route path="/assets" element={<Assets />} /> */}
          {/* <Route path="/services" element={<Services />} /> */}
          {/* <Route path="/kanban" element={<Kanban />} /> */}
          {/* <Route path="/calendar" element={<Calendar />} /> */}
          {/* <Route path="/settings" element={<Settings />} /> */}
        </Route>

        {/* Default */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
