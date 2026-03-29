import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const formatDateTime = (value: string | null | undefined): string => {
  if (!value) {
    return "-";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }

  return parsed.toLocaleString();
};

const formatWorkspaceAge = (value: string | null | undefined): string => {
  if (!value) {
    return "-";
  }

  const createdAt = new Date(value);
  if (Number.isNaN(createdAt.getTime())) {
    return "-";
  }

  const ageMs = Date.now() - createdAt.getTime();
  if (ageMs <= 0) {
    return "Today";
  }

  const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24));
  return `${ageDays} day${ageDays === 1 ? "" : "s"}`;
};

export const AdminSettingsPage = () => {
  const { company, user } = useAuth();

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Company Settings</h2>
          <p className="muted">
            Workspace profile, admin shortcuts, and a readiness checklist for operations.
          </p>
        </div>
      </div>

      <div className="settings-grid">
        <article className="settings-card">
          <h3>Workspace Profile</h3>
          <div className="settings-row">
            <span className="muted">Company</span>
            <strong>{company?.name ?? "-"}</strong>
          </div>
          <div className="settings-row">
            <span className="muted">Country Code</span>
            <strong>{company?.country_code ?? "-"}</strong>
          </div>
          <div className="settings-row">
            <span className="muted">Base Currency</span>
            <strong>{company?.base_currency ?? "-"}</strong>
          </div>
          <div className="settings-row">
            <span className="muted">Created</span>
            <strong>{formatDateTime(company?.created_at)}</strong>
          </div>
          <div className="settings-row">
            <span className="muted">Workspace Age</span>
            <strong>{formatWorkspaceAge(company?.created_at)}</strong>
          </div>
          <div className="settings-row">
            <span className="muted">Primary Admin</span>
            <strong>
              {user?.first_name} {user?.last_name}
            </strong>
          </div>
        </article>

        <article className="settings-card">
          <h3>Admin Shortcuts</h3>
          <p className="muted">
            Keep master data and approval routing fresh before monthly close.
          </p>
          <div className="quick-actions">
            <Link to="/admin/users" className="secondary-link-btn">
              Manage Users
            </Link>
            <Link to="/admin/departments" className="secondary-link-btn">
              Departments
            </Link>
            <Link to="/admin/categories" className="secondary-link-btn">
              Categories
            </Link>
            <Link to="/admin/rules" className="secondary-link-btn">
              Approval Rules
            </Link>
          </div>
        </article>
      </div>

      <section className="admin-form-card">
        <h3>Operations Checklist</h3>
        <ul className="settings-list">
          <li>Review pending approvals and escalations in Approvals Inbox.</li>
          <li>Confirm every active employee has department and manager assignment.</li>
          <li>Audit category and approval rule mappings for high-value expense types.</li>
          <li>Spot-check currency conversion outcomes in recent multi-currency claims.</li>
        </ul>
      </section>
    </div>
  );
};
