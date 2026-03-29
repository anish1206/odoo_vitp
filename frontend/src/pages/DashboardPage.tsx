import { Link } from "react-router-dom";

export const DashboardPage = () => {
  return (
    <div>
      <h2>Employee Dashboard</h2>
      <p className="muted">
        Phase 3 now supports creating claim drafts, editing drafts, submitting claims,
        and filtering your claim history.
      </p>

      <div className="stats-grid">
        <article className="stat-card">
          <h3>Claims This Month</h3>
          <p className="stat-value">0</p>
        </article>
        <article className="stat-card">
          <h3>Pending Approvals</h3>
          <p className="stat-value">0</p>
        </article>
        <article className="stat-card">
          <h3>Rejected</h3>
          <p className="stat-value">0</p>
        </article>
      </div>

      <div className="quick-actions">
        <Link to="/employee/submit" className="primary-link-btn">
          Submit New Expense
        </Link>
        <Link to="/employee/claims" className="secondary-link-btn">
          View My Claims
        </Link>
      </div>
    </div>
  );
};
