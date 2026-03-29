import { http } from "./http";
import type {
  ApprovalRule,
  ApprovalRuleCreatePayload,
  ApprovalRuleStepPayload,
  ApprovalRuleUpdatePayload,
} from "../types/approvalRules";

export const listApprovalRules = async (): Promise<ApprovalRule[]> => {
  const response = await http.get<ApprovalRule[]>("/approval-rules");
  return response.data;
};

export const createApprovalRule = async (
  payload: ApprovalRuleCreatePayload,
): Promise<ApprovalRule> => {
  const response = await http.post<ApprovalRule>("/approval-rules", payload);
  return response.data;
};

export const updateApprovalRule = async (
  ruleId: number,
  payload: ApprovalRuleUpdatePayload,
): Promise<ApprovalRule> => {
  const response = await http.patch<ApprovalRule>(`/approval-rules/${ruleId}`, payload);
  return response.data;
};

export const replaceApprovalRuleSteps = async (
  ruleId: number,
  steps: ApprovalRuleStepPayload[],
): Promise<ApprovalRule> => {
  const response = await http.put<ApprovalRule>(`/approval-rules/${ruleId}/steps`, { steps });
  return response.data;
};
