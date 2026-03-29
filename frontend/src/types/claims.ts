export type ClaimStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "IN_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "CANCELLED";

export interface ExpenseCategory {
  id: number;
  name: string;
  code: string | null;
  description: string | null;
}

export interface Claim {
  id: number;
  title: string;
  description: string | null;
  category_id: number;
  category_name: string;
  receipt_file_id: number | null;
  original_currency: string;
  original_amount: number;
  base_currency: string;
  converted_amount: number | null;
  exchange_rate_snapshot_id: number | null;
  exchange_rate: number | null;
  exchange_rate_provider: string | null;
  exchange_rate_as_of: string | null;
  expense_date: string;
  status: ClaimStatus;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
  is_editable: boolean;
  employee_id: number | null;
  employee_name: string | null;
  department_id: number | null;
  department_name: string | null;
  pending_approver_names: string[];
}

export interface ClaimListResponse {
  claims: Claim[];
}

export interface ClaimApprovalTask {
  task_id: number;
  sequence_order: number;
  status: string;
  approver_id: number | null;
  approver_name: string | null;
  acted_at: string | null;
  comment: string | null;
}

export interface ClaimTimelineEvent {
  id: number;
  action_type: string;
  actor_name: string | null;
  description: string | null;
  created_at: string;
}

export interface ClaimReceiptContext {
  receipt_id: number;
  original_filename: string;
  file_mime_type: string;
  file_size_bytes: number;
  uploaded_at: string;
}

export interface ClaimOcrContext {
  extraction_id: number;
  engine: string | null;
  confidence: number | null;
  parsed_fields: Record<string, unknown> | null;
  created_at: string;
}

export interface ClaimDetail extends Claim {
  rejection_reason: string | null;
  current_approval_step: number | null;
  final_approved_at: string | null;
  approval_tasks: ClaimApprovalTask[];
  approval_timeline: ClaimTimelineEvent[];
  receipt: ClaimReceiptContext | null;
  ocr_extraction: ClaimOcrContext | null;
}

export interface ClaimCreateRequest {
  title: string;
  description?: string | null;
  category_id: number;
  receipt_file_id?: number | null;
  original_currency: string;
  original_amount: number;
  expense_date: string;
  department_id?: number | null;
}

export interface ClaimUpdateRequest {
  title?: string;
  description?: string | null;
  category_id?: number;
  receipt_file_id?: number | null;
  original_currency?: string;
  original_amount?: number;
  expense_date?: string;
  department_id?: number | null;
}
