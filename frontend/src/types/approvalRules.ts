export type ApprovalRuleStrategy = "SEQUENTIAL" | "MIN_APPROVALS";
export type StepApproverRole = "MANAGER" | "SPECIFIC_USER" | "DEPARTMENT_HEAD";

export interface ApprovalRuleStep {
  id: number;
  rule_id: number;
  step_order: number;
  name: string;
  approver_role: StepApproverRole;
  approver_user_id: number | null;
  approver_department_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRule {
  id: number;
  company_id: number;
  name: string;
  description: string | null;
  min_amount: number | null;
  max_amount: number | null;
  category_id: number | null;
  department_id: number | null;
  strategy: ApprovalRuleStrategy;
  min_approval_percentage: number | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
  steps: ApprovalRuleStep[];
}

export interface ApprovalRuleStepPayload {
  step_order: number;
  name: string;
  approver_role: StepApproverRole;
  approver_user_id: number | null;
  approver_department_id: number | null;
}

export interface ApprovalRuleCreatePayload {
  name: string;
  description?: string | null;
  min_amount?: number | null;
  max_amount?: number | null;
  category_id?: number | null;
  department_id?: number | null;
  strategy: ApprovalRuleStrategy;
  min_approval_percentage?: number | null;
  is_active: boolean;
  priority: number;
  steps: ApprovalRuleStepPayload[];
}

export interface ApprovalRuleUpdatePayload {
  name?: string;
  description?: string | null;
  min_amount?: number | null;
  max_amount?: number | null;
  category_id?: number | null;
  department_id?: number | null;
  strategy?: ApprovalRuleStrategy;
  min_approval_percentage?: number | null;
  is_active?: boolean;
  priority?: number;
}
