export type ApprovalTaskStatus = "PENDING" | "APPROVED" | "REJECTED" | "SKIPPED";

export interface ApprovalTaskSummary {
  task_id: number;
  claim_id: number;
  claim_title: string;
  employee_name: string;
  category_name: string;
  original_currency: string;
  original_amount: number;
  submitted_at: string | null;
  sequence_order: number;
  status: ApprovalTaskStatus;
  is_actionable: boolean;
}

export interface ApprovalTaskListResponse {
  tasks: ApprovalTaskSummary[];
}

export interface ApprovalActionLog {
  id: number;
  action_type: string;
  actor_name: string | null;
  description: string | null;
  created_at: string;
}

export interface ApprovalTaskClaimDetail {
  task_id: number;
  claim_id: number;
  employee_name: string;
  claim_title: string;
  claim_description: string | null;
  category_name: string;
  expense_date: string;
  original_currency: string;
  original_amount: number;
  status: string;
  current_approval_step: number | null;
  logs: ApprovalActionLog[];
}

export interface ApprovalDecisionPayload {
  comment?: string | null;
}

export interface ApprovalDecisionResponse {
  task_id: number;
  task_status: ApprovalTaskStatus;
  claim_id: number;
  claim_status: string;
}
