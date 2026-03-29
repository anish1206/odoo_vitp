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

export interface ApprovalReceiptContext {
  receipt_id: number;
  original_filename: string;
  file_mime_type: string;
  file_size_bytes: number;
  uploaded_at: string;
}

export interface ApprovalOcrContext {
  extraction_id: number;
  engine: string | null;
  confidence: number | null;
  parsed_fields: Record<string, unknown> | null;
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
  base_currency: string;
  converted_amount: number | null;
  exchange_rate: number | null;
  exchange_rate_provider: string | null;
  status: string;
  current_approval_step: number | null;
  pending_approver_names: string[];
  receipt: ApprovalReceiptContext | null;
  ocr_extraction: ApprovalOcrContext | null;
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
