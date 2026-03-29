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
}

export interface ClaimListResponse {
  claims: Claim[];
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
