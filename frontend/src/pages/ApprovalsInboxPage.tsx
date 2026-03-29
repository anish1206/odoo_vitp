import axios from "axios";
import { useEffect, useState } from "react";

import {
  approveTask,
  getApprovalTaskDetail,
  listApprovalTasks,
  rejectTask,
} from "../api/approvals";
import type {
  ApprovalTaskClaimDetail,
  ApprovalTaskStatus,
  ApprovalTaskSummary,
} from "../types/approvals";

const statusOptions: ApprovalTaskStatus[] = [
  "PENDING",
  "APPROVED",
  "REJECTED",
  "SKIPPED",
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

export const ApprovalsInboxPage = () => {
  const [tasks, setTasks] = useState<ApprovalTaskSummary[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [taskDetail, setTaskDetail] = useState<ApprovalTaskClaimDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<ApprovalTaskStatus>("PENDING");
  const [comment, setComment] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isActing, setIsActing] = useState(false);
  const [error, setError] = useState("");

  const loadInbox = async () => {
    setError("");
    setIsLoading(true);

    try {
      const response = await listApprovalTasks(statusFilter);
      setTasks(response.tasks);

      const nextSelectedTaskId = response.tasks[0]?.task_id ?? null;
      setSelectedTaskId(nextSelectedTaskId);

      if (nextSelectedTaskId !== null) {
        const detail = await getApprovalTaskDetail(nextSelectedTaskId);
        setTaskDetail(detail);
      } else {
        setTaskDetail(null);
      }
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load approvals inbox."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadInbox();
  }, [statusFilter]);

  const selectedTask = tasks.find((task) => task.task_id === selectedTaskId) ?? null;
  const canActOnTask = statusFilter === "PENDING" && selectedTask?.is_actionable === true;

  const onSelectTask = async (taskId: number) => {
    setError("");
    setSelectedTaskId(taskId);

    try {
      const detail = await getApprovalTaskDetail(taskId);
      setTaskDetail(detail);
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load claim detail."));
    }
  };

  const onApprove = async () => {
    if (selectedTaskId === null) {
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await approveTask(selectedTaskId, { comment: comment.trim() || null });
      setComment("");
      await loadInbox();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to approve task."));
    } finally {
      setIsActing(false);
    }
  };

  const onReject = async () => {
    if (selectedTaskId === null) {
      return;
    }

    if (!comment.trim()) {
      setError("Rejection comment is required.");
      return;
    }

    setIsActing(true);
    setError("");

    try {
      await rejectTask(selectedTaskId, { comment: comment.trim() });
      setComment("");
      await loadInbox();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to reject task."));
    } finally {
      setIsActing(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Approvals Inbox</h2>
          <p className="muted">Review pending and completed approvals assigned to you.</p>
        </div>
      </div>

      <div className="filters-row">
        <div>
          <label htmlFor="approvalStatus">Status</label>
          <select
            id="approvalStatus"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as ApprovalTaskStatus)}
          >
            {statusOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      {isLoading ? (
        <div className="centered-page">Loading approvals...</div>
      ) : tasks.length === 0 ? (
        <p className="muted">No {statusFilter.toLowerCase()} approvals found.</p>
      ) : (
        <div className="approval-layout">
          <div className="approval-list">
            {tasks.map((task) => (
              <button
                key={task.task_id}
                type="button"
                className={
                  selectedTaskId === task.task_id
                    ? "approval-task-button approval-task-button-active"
                    : "approval-task-button"
                }
                onClick={() => void onSelectTask(task.task_id)}
              >
                <strong>{task.claim_title}</strong>
                <span className="muted">{task.employee_name}</span>
                <span>
                  {task.original_currency} {task.original_amount.toFixed(2)}
                </span>
              </button>
            ))}
          </div>

          <div className="approval-detail">
            {taskDetail ? (
              <>
                <h3>{taskDetail.claim_title}</h3>
                <p className="muted">Employee: {taskDetail.employee_name}</p>
                <p className="muted">Category: {taskDetail.category_name}</p>
                <p>
                  Amount: {taskDetail.original_currency} {taskDetail.original_amount.toFixed(2)}
                </p>
                <p>Expense date: {taskDetail.expense_date}</p>
                {taskDetail.claim_description ? <p>{taskDetail.claim_description}</p> : null}

                <label htmlFor="approvalComment">Comment (required for rejection)</label>
                <textarea
                  id="approvalComment"
                  className="text-area"
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Add optional approval note or required rejection reason"
                  disabled={!canActOnTask}
                />

                <div className="quick-actions">
                  <button
                    type="button"
                    className="secondary-link-btn"
                    onClick={onReject}
                    disabled={isActing || !canActOnTask}
                  >
                    {isActing ? "Processing..." : "Reject"}
                  </button>
                  <button
                    type="button"
                    className="primary-link-btn"
                    onClick={onApprove}
                    disabled={isActing || !canActOnTask}
                  >
                    {isActing ? "Processing..." : "Approve"}
                  </button>
                </div>

                <h4>Timeline</h4>
                <div className="timeline-list">
                  {taskDetail.logs.map((log) => (
                    <div key={log.id} className="timeline-item">
                      <strong>{log.action_type}</strong>
                      <p className="muted">
                        {log.actor_name ?? "System"} · {new Date(log.created_at).toLocaleString()}
                      </p>
                      {log.description ? <p>{log.description}</p> : null}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="muted">Select a task to review claim details.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
