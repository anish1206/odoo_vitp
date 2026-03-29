import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { listApprovalTasks } from "../api/approvals";
import { listMyClaims } from "../api/claims";
import { useAuth } from "../context/AuthContext";

interface DashboardStats {
  claimsThisMonth: number;
  pendingApprovals: number;
  rejectedClaims: number;
}

const EMPTY_STATS: DashboardStats = {
  claimsThisMonth: 0,
  pendingApprovals: 0,
  rejectedClaims: 0,
};

const isCurrentMonth = (value: string): boolean => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return false;
  }

  const now = new Date();
  return parsed.getMonth() === now.getMonth() && parsed.getFullYear() === now.getFullYear();
};

export const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const canReviewApprovals = useMemo(
    () => Boolean(user?.is_approver || user?.role === "ADMIN"),
    [user?.is_approver, user?.role],
  );

  useEffect(() => {
    let isCancelled = false;

    const loadDashboard = async () => {
      setError("");
      setIsLoading(true);

      try {
        const [claimsResponse, approvalsResponse] = await Promise.all([
          listMyClaims(),
          canReviewApprovals
            ? listApprovalTasks("PENDING")
            : Promise.resolve({ tasks: [] }),
        ]);

        if (isCancelled) {
          return;
        }

        const claims = claimsResponse.claims;
        const claimsThisMonth = claims.filter((claim) => isCurrentMonth(claim.expense_date)).length;
        const rejectedClaims = claims.filter((claim) => claim.status === "REJECTED").length;

        setStats({
          claimsThisMonth,
          pendingApprovals: approvalsResponse.tasks.length,
          rejectedClaims,
        });
      } catch {
        if (!isCancelled) {
          setStats(EMPTY_STATS);
          setError("Unable to load dashboard metrics right now.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => {
      isCancelled = true;
    };
  }, [canReviewApprovals]);

  return (
    <div>
      <h2>Employee Dashboard</h2>
      <p className="muted">
        Track spend, monitor approvals, and jump directly into your daily expense actions.
      </p>
      {error ? <p className="error-text">{error}</p> : null}

      <div className="stats-grid">
        <article className="stat-card">
          <h3>Claims This Month</h3>
          <p className="stat-value">{isLoading ? "..." : stats.claimsThisMonth}</p>
        </article>
        <article className="stat-card">
          <h3>Pending Approvals</h3>
          <p className="stat-value">{isLoading ? "..." : stats.pendingApprovals}</p>
        </article>
        <article className="stat-card">
          <h3>Rejected</h3>
          <p className="stat-value">{isLoading ? "..." : stats.rejectedClaims}</p>
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
