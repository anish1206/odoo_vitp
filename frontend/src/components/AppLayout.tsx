import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

interface NavItem {
  to: string;
  label: string;
}

export const AppLayout = () => {
  const { user, company, logout } = useAuth();

  const navItems: NavItem[] = [
    { to: "/employee/dashboard", label: "Employee Dashboard" },
    { to: "/employee/claims", label: "My Claims" },
    { to: "/employee/submit", label: "Submit Expense" },
  ];

  if (user?.is_approver || user?.role === "ADMIN") {
    navItems.push({ to: "/approvals/inbox", label: "Approvals Inbox" });
  }

  if (user?.role === "ADMIN") {
    navItems.push(
      { to: "/admin/settings", label: "Company Settings" },
      { to: "/admin/claims", label: "All Claims" },
      { to: "/admin/users", label: "Users" },
      { to: "/admin/departments", label: "Departments" },
      { to: "/admin/categories", label: "Categories" },
      { to: "/admin/rules", label: "Approval Rules" },
    );
  }

  const roleLabel =
    user?.role === "ADMIN"
      ? user.is_approver
        ? "ADMIN + APPROVER"
        : "ADMIN"
      : user?.is_approver
        ? "EMPLOYEE + APPROVER"
        : "EMPLOYEE";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>ReimburseFlow</h1>
        <p className="muted">Expense operations workspace</p>
        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "nav-link nav-link-active" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="muted">Company</p>
            <strong>{company?.name ?? "-"}</strong>
          </div>
          <div className="topbar-right">
            <span className="role-badge">{roleLabel}</span>
            <div>
              <p className="muted">Signed in as</p>
              <strong>
                {user?.first_name} {user?.last_name}
              </strong>
            </div>
            <button type="button" className="ghost-btn" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
        <section className="view-panel">
          <Outlet />
        </section>
      </main>
    </div>
  );
};
