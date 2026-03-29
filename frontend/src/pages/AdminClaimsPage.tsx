import axios from "axios";
import { useEffect, useMemo, useState } from "react";

import { getCompanyClaimDetail, listCompanyClaims } from "../api/claims";
import type { Claim, ClaimDetail, ClaimStatus } from "../types/claims";

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

export const AdminClaimsPage = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<number | null>(null);
  const [claimDetail, setClaimDetail] = useState<ClaimDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<"" | ClaimStatus>("");
  const [employeeFilter, setEmployeeFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  const employeeOptions = useMemo(() => {
    const map = new Map<number, string>();
    claims.forEach((claim) => {
      if (claim.employee_id !== null) {
        map.set(claim.employee_id, claim.employee_name ?? `User #${claim.employee_id}`);
      }
    });

    return [...map.entries()]
      .map(([id, name]) => ({ id, name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [claims]);

  const onSelectClaim = async (claimId: number) => {
    setError("");
    setSelectedClaimId(claimId);
    setIsLoadingDetail(true);

    try {
      const detail = await getCompanyClaimDetail(claimId);
      setClaimDetail(detail);
    } catch (unknownError) {
      setClaimDetail(null);
      setError(getApiErrorMessage(unknownError, "Unable to load claim detail."));
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const loadClaims = async () => {
    setError("");
    setIsLoading(true);

    try {
      const response = await listCompanyClaims({
        status: statusFilter || undefined,
        employee_id: employeeFilter ? Number(employeeFilter) : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setClaims(response.claims);

      if (response.claims.length === 0) {
        setSelectedClaimId(null);
        setClaimDetail(null);
      } else if (
        selectedClaimId === null ||
        !response.claims.some((claim) => claim.id === selectedClaimId)
      ) {
        const firstClaimId = response.claims[0].id;
        await onSelectClaim(firstClaimId);
      }
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load company claims."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadClaims();
  }, [statusFilter]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>All Claims</h2>
          <p className="muted">Company-wide visibility for admin review and audit readiness.</p>
        </div>
      </div>

      <div className="filters-row filters-row-wide">
        <div>
          <label htmlFor="adminClaimsStatus">Status</label>
          <select
            id="adminClaimsStatus"
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
          <label htmlFor="adminEmployeeFilter">Employee</label>
          <select
            id="adminEmployeeFilter"
            value={employeeFilter}
            onChange={(event) => setEmployeeFilter(event.target.value)}
          >
            <option value="">All employees</option>
            {employeeOptions.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="adminDateFrom">From</label>
          <input
            id="adminDateFrom"
            type="date"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
          />
        </div>

        <div>
          <label htmlFor="adminDateTo">To</label>
          <input
            id="adminDateTo"
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
        <div className="centered-page">Loading company claims...</div>
      ) : claims.length === 0 ? (
        <p className="muted">No claims match the selected filters.</p>
      ) : (
        <div className="approval-layout">
          <div className="approval-list">
            {claims.map((claim) => (
              <button
                key={claim.id}
                type="button"
                className={
                  selectedClaimId === claim.id
                    ? "approval-task-button approval-task-button-active"
                    : "approval-task-button"
                }
                onClick={() => void onSelectClaim(claim.id)}
              >
                <strong>{claim.title}</strong>
                <span className="muted">{claim.employee_name ?? "Unknown employee"}</span>
                <span>{claim.category_name}</span>
                <span>
                  {claim.original_currency} {claim.original_amount.toFixed(2)}
                </span>
                <span className="muted">{claim.status}</span>
              </button>
            ))}
          </div>

          <div className="approval-detail">
            {isLoadingDetail ? (
              <p className="muted">Loading claim detail...</p>
            ) : claimDetail ? (
              <>
                <h3>{claimDetail.title}</h3>
                <p className="muted">
                  {claimDetail.employee_name ?? "Unknown employee"}
                  {claimDetail.department_name ? ` · ${claimDetail.department_name}` : ""}
                </p>
                <p className="muted">
                  Status: {claimDetail.status}
                  {claimDetail.pending_approver_names.length > 0
                    ? ` · Pending with ${claimDetail.pending_approver_names.join(", ")}`
                    : ""}
                </p>
                <p>
                  Amount: {claimDetail.original_currency} {claimDetail.original_amount.toFixed(2)}
                </p>
                {claimDetail.converted_amount !== null ? (
                  <p>
                    Converted: {claimDetail.base_currency} {claimDetail.converted_amount.toFixed(2)}
                    {claimDetail.exchange_rate !== null ? (
                      <span className="muted"> (rate {claimDetail.exchange_rate.toFixed(4)})</span>
                    ) : null}
                  </p>
                ) : null}

                {claimDetail.rejection_reason ? (
                  <p className="error-text">Rejection reason: {claimDetail.rejection_reason}</p>
                ) : null}

                {claimDetail.receipt ? (
                  <div className="context-card">
                    <h4>Receipt</h4>
                    <p>
                      <strong>{claimDetail.receipt.original_filename}</strong>
                    </p>
                    <p className="muted">
                      {claimDetail.receipt.file_mime_type} · {claimDetail.receipt.file_size_bytes} bytes
                    </p>
                  </div>
                ) : (
                  <p className="muted">No receipt attached.</p>
                )}

                {claimDetail.ocr_extraction ? (
                  <div className="context-card">
                    <h4>OCR Extraction</h4>
                    <p className="muted">
                      Engine: {claimDetail.ocr_extraction.engine ?? "unknown"}
                      {claimDetail.ocr_extraction.confidence !== null
                        ? ` · confidence ${Math.round(claimDetail.ocr_extraction.confidence * 100)}%`
                        : ""}
                    </p>
                    {claimDetail.ocr_extraction.parsed_fields ? (
                      <pre className="ocr-pre">
                        {JSON.stringify(claimDetail.ocr_extraction.parsed_fields, null, 2)}
                      </pre>
                    ) : (
                      <p className="muted">No structured OCR fields available.</p>
                    )}
                  </div>
                ) : null}

                <h4>Approval Tasks</h4>
                {claimDetail.approval_tasks.length === 0 ? (
                  <p className="muted">No approval tasks created yet.</p>
                ) : (
                  <div className="timeline-list">
                    {claimDetail.approval_tasks.map((task) => (
                      <div key={task.task_id} className="timeline-item">
                        <strong>
                          Step {task.sequence_order}: {task.approver_name ?? "Pending assignment"}
                        </strong>
                        <p className="muted">{task.status}</p>
                        {task.comment ? <p>{task.comment}</p> : null}
                      </div>
                    ))}
                  </div>
                )}

                <h4>Timeline</h4>
                {claimDetail.approval_timeline.length === 0 ? (
                  <p className="muted">No timeline events yet.</p>
                ) : (
                  <div className="timeline-list">
                    {claimDetail.approval_timeline.map((event) => (
                      <div key={event.id} className="timeline-item">
                        <strong>{event.action_type}</strong>
                        <p className="muted">
                          {event.actor_name ?? "System"} · {new Date(event.created_at).toLocaleString()}
                        </p>
                        {event.description ? <p>{event.description}</p> : null}
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p className="muted">Select a claim to inspect details.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
