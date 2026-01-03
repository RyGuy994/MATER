// MATER/MATER_FE/src/layouts/AppLayout.jsx
import { NavLink, Outlet } from "react-router-dom";
import "./AppLayout.css";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/assets", label: "Assets" },
  { to: "/services", label: "Services" },
  { to: "/kanban", label: "KanBan" },
  { to: "/calendar", label: "Calendar" },
  { to: "/settings", label: "User Settings" },
];

export default function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-brand">
          <img src="/MATER.png" alt="MATER" className="app-brand-logo" />
          <div className="app-brand-text">
            <div className="app-brand-title">MATER</div>
            <div className="app-brand-subtitle">Control Center</div>
          </div>
        </div>

        <nav className="app-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `app-nav-link${isActive ? " is-active" : ""}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
