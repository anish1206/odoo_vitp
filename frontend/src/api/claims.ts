import { http } from "./http";
import type {
  Claim,
  ClaimCreateRequest,
  ClaimListResponse,
  ClaimStatus,
  ClaimUpdateRequest,
  ExpenseCategory,
} from "../types/claims";

export interface ClaimListFilters {
  status?: ClaimStatus;
  date_from?: string;
  date_to?: string;
}

export const listClaimCategories = async (): Promise<ExpenseCategory[]> => {
  const response = await http.get<ExpenseCategory[]>("/claims/categories");
  return response.data;
};

export const createClaim = async (payload: ClaimCreateRequest): Promise<Claim> => {
  const response = await http.post<Claim>("/claims", payload);
  return response.data;
};

export const updateDraftClaim = async (
  claimId: number,
  payload: ClaimUpdateRequest,
): Promise<Claim> => {
  const response = await http.patch<Claim>(`/claims/${claimId}`, payload);
  return response.data;
};

export const submitClaim = async (claimId: number): Promise<Claim> => {
  const response = await http.post<Claim>(`/claims/${claimId}/submit`);
  return response.data;
};

export const getClaimDetail = async (claimId: number): Promise<Claim> => {
  const response = await http.get<Claim>(`/claims/${claimId}`);
  return response.data;
};

export const listMyClaims = async (
  filters: ClaimListFilters = {},
): Promise<ClaimListResponse> => {
  const response = await http.get<ClaimListResponse>("/claims/my", {
    params: filters,
  });
  return response.data;
};
