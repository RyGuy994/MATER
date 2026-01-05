// filepath: MATER/MATER_FE/src/layouts/AppLayout.jsx
import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import "./AppLayout.css";

const IconDashboard = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M3 13h8V3H3v10z" />
    <path d="M13 21h8V11h-8v10z" />
    <path d="M13 3h8v6h-8V3z" />
    <path d="M3 17h8v4H3v-4z" />
  </svg>
);

const IconAssets = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M21 16V8a2 2 0 0 0-1-1.73L13 2.27a2 2 0 0 0-2 0L4 6.27A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
    <path d="M3.3 7.3 12 12l8.7-4.7" />
    <path d="M12 22V12" />
  </svg>
);

const IconServices = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4l-6 6a2 2 0 1 0 2.8 2.8l6-6a4 4 0 0 0 5.4-5.4l-3 3-2.8-2.8 3-3z" />
  </svg>
);

const IconKanban = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M4 5h6v14H4V5z" />
    <path d="M14 5h6v8h-6V5z" />
    <path d="M14 17h6v2h-6v-2z" />
  </svg>
);

const IconCalendar = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M8 2v3M16 2v3" />
    <path d="M3 8h18" />
    <path d="M5 5h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" />
  </svg>
);

const IconSettings = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
    <path d="M19.4 15a7.9 7.9 0 0 0 .1-6l2-1.5-2-3.5-2.4 1a8.2 8.2 0 0 0-5.2-3L11.5 0h-4L7 2a8.2 8.2 0 0 0-5.2 3L-.6 4.0-2.6 7.5-.6 9a7.9 7.9 0 0 0 .1 6l-2 1.5 2 3.5 2.4-1a8.2 8.2 0 0 0 5.2 3l.5 2h4l.5-2a8.2 8.2 0 0 0 5.2-3l2.4 1 2-3.5-2-1.5z" />
  </svg>
);

const navItems = [
  { to: "/dashboard", label: "Dashboard", Icon: IconDashboard },
  { to: "/assets", label: "Assets", Icon: IconAssets },
  { to: "/services", label: "Services", Icon: IconServices },
  { to: "/kanban", label: "KanBan", Icon: IconKanban },
  { to: "/calendar", label: "Calendar", Icon: IconCalendar },
  { to: "/settings", label: "User Settings", Icon: IconSettings },
];

const SIDEBAR_KEY = "mater_sidebar_collapsed";

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(SIDEBAR_KEY) === "1");

  useEffect(() => {
    localStorage.setItem(SIDEBAR_KEY, collapsed ? "1" : "0");
  }, [collapsed]);

  return (
    <div className={`app-shell${collapsed ? " is-collapsed" : ""}`}>
      <aside className="app-sidebar">
        <button
          type="button"
          className="app-brand app-brand-button"
          onClick={() => setCollapsed((v) => !v)}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <img src="/MATER.png" alt="MATER" className="app-brand-logo" />
          <div className="app-brand-text">
            <div className="app-brand-title">MATER</div>
            <div className="app-brand-subtitle">Control Center</div>
          </div>
        </button>

        <nav className="app-nav" aria-label="Primary">
          {navItems.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `app-nav-link${isActive ? " is-active" : ""}`}
              title={collapsed ? label : undefined}
            >
              <Icon className="app-nav-icon" aria-hidden="true" />
              <span className="app-nav-label">{label}</span>
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
