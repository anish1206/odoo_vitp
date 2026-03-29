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
  original_currency: string;
  original_amount: number;
  base_currency: string;
  converted_amount: number | null;
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
  original_currency: string;
  original_amount: number;
  expense_date: string;
  department_id?: number | null;
}

export interface ClaimUpdateRequest {
  title?: string;
  description?: string | null;
  category_id?: number;
  original_currency?: string;
  original_amount?: number;
  expense_date?: string;
  department_id?: number | null;
}
