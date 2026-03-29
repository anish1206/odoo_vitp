import { http } from "./http";
import type {
  ApprovalDecisionPayload,
  ApprovalDecisionResponse,
  ApprovalTaskStatus,
  ApprovalTaskClaimDetail,
  ApprovalTaskListResponse,
} from "../types/approvals";

export const listApprovalTasks = async (
  status: ApprovalTaskStatus = "PENDING",
): Promise<ApprovalTaskListResponse> => {
  const response = await http.get<ApprovalTaskListResponse>("/approvals/tasks", {
    params: { status },
  });
  return response.data;
};

export const getApprovalTaskDetail = async (
  taskId: number,
): Promise<ApprovalTaskClaimDetail> => {
  const response = await http.get<ApprovalTaskClaimDetail>(`/approvals/tasks/${taskId}`);
  return response.data;
};

export const approveTask = async (
  taskId: number,
  payload: ApprovalDecisionPayload,
): Promise<ApprovalDecisionResponse> => {
  const response = await http.post<ApprovalDecisionResponse>(
    `/approvals/tasks/${taskId}/approve`,
    payload,
  );
  return response.data;
};

export const rejectTask = async (
  taskId: number,
  payload: ApprovalDecisionPayload,
): Promise<ApprovalDecisionResponse> => {
  const response = await http.post<ApprovalDecisionResponse>(
    `/approvals/tasks/${taskId}/reject`,
    payload,
  );
  return response.data;
};
