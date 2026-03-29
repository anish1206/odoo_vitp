import axios from "axios";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listMyClaims, submitClaim } from "../api/claims";
import type { Claim, ClaimStatus } from "../types/claims";

const statusOptions: Array<{ value: "" | ClaimStatus; label: string }> = [
  { value: "", label: "All" },
  { value: "DRAFT", label: "Draft" },
  { value: "SUBMITTED", label: "Submitted" },
  { value: "IN_REVIEW", label: "In Review" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
  { value: "CANCELLED", label: "Cancelled" },
];

const getApiErrorMessage = (unknownError: unknown, fallback: string): string => {
  if (!axios.isAxiosError(unknownError)) {
    return fallback;
  }

  const detail = unknownError.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  return fallback;
};

export const EmployeeClaimsPage = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [statusFilter, setStatusFilter] = useState<"" | ClaimStatus>("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadClaims = async () => {
    setError("");
    setIsLoading(true);

    try {
      const response = await listMyClaims({
        status: statusFilter || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setClaims(response.claims);
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load claims."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadClaims();
  }, []);

  const onSubmitDraft = async (claimId: number) => {
    setError("");
    try {
      await submitClaim(claimId);
      await loadClaims();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to submit draft."));
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>My Claims</h2>
          <p className="muted">Track drafts and submitted expenses.</p>
        </div>
        <Link to="/employee/submit" className="primary-link-btn">
          New Claim
        </Link>
      </div>

      <div className="filters-row">
        <div>
          <label htmlFor="statusFilter">Status</label>
          <select
            id="statusFilter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as "" | ClaimStatus)}
          >
            {statusOptions.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="dateFrom">From</label>
          <input
            id="dateFrom"
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
          />
        </div>

        <div>
          <label htmlFor="dateTo">To</label>
          <input
            id="dateTo"
            type="date"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
          />
        </div>

        <div className="filter-buttons">
          <button type="button" className="secondary-link-btn" onClick={() => void loadClaims()}>
            Apply Filters
          </button>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      {isLoading ? (
        <div className="centered-page">Loading claims...</div>
      ) : claims.length === 0 ? (
        <p className="muted">No claims yet. Create your first draft.</p>
      ) : (
        <div className="table-wrap">
          <table className="claims-table">
            <thead>
              <tr>
                <th>Expense Date</th>
                <th>Title</th>
                <th>Category</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim) => (
                <tr key={claim.id}>
                  <td>{claim.expense_date}</td>
                  <td>{claim.title}</td>
                  <td>{claim.category_name}</td>
                  <td>
                    {claim.original_currency} {claim.original_amount.toFixed(2)}
                  </td>
                  <td>
                    <span className="role-badge">{claim.status}</span>
                  </td>
                  <td className="row-actions">
                    {claim.is_editable ? (
                      <>
                        <Link to={`/employee/submit?claimId=${claim.id}`} className="secondary-link-btn">
                          Edit Draft
                        </Link>
                        <button
                          type="button"
                          className="primary-link-btn"
                          onClick={() => void onSubmitDraft(claim.id)}
                        >
                          Submit
                        </button>
                      </>
                    ) : (
                      <span className="muted">No actions</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
