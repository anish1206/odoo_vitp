import axios from "axios";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import {
  createClaim,
  getClaimDetail,
  listClaimCategories,
  submitClaim,
  updateDraftClaim,
} from "../api/claims";
import type { ClaimCreateRequest, ExpenseCategory } from "../types/claims";

interface ClaimFormState {
  title: string;
  description: string;
  category_id: string;
  original_currency: string;
  original_amount: string;
  expense_date: string;
}

const initialFormState: ClaimFormState = {
  title: "",
  description: "",
  category_id: "",
  original_currency: "INR",
  original_amount: "",
  expense_date: new Date().toISOString().slice(0, 10),
};

const defaultErrorMessage = "Unable to save claim. Please try again.";

const parseClaimId = (rawClaimId: string | null): number | null => {
  if (!rawClaimId) {
    return null;
  }

  const parsed = Number(rawClaimId);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }

  return parsed;
};

const getApiErrorMessage = (unknownError: unknown, fallback: string): string => {
  if (!axios.isAxiosError(unknownError)) {
    return fallback;
  }

  const detail = unknownError.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first && typeof first === "object" && "msg" in first) {
      const message = first.msg;
      if (typeof message === "string" && message.trim()) {
        return message;
      }
    }
  }

  return fallback;
};

export const EmployeeSubmitClaimPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const claimId = useMemo(() => parseClaimId(searchParams.get("claimId")), [searchParams]);
  const isEditing = claimId !== null;

  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [form, setForm] = useState<ClaimFormState>(initialFormState);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    const loadData = async () => {
      setError("");
      setSuccessMessage("");
      setIsLoading(true);

      try {
        const categoriesResponse = await listClaimCategories();
        setCategories(categoriesResponse);

        const firstCategoryId = categoriesResponse[0]?.id;

        if (!isEditing) {
          setForm((previous) => {
            if (previous.category_id || firstCategoryId === undefined) {
              return previous;
            }

            return {
              ...previous,
              category_id: String(firstCategoryId),
            };
          });
          return;
        }

        const editingClaimId = claimId;
        if (editingClaimId === null) {
          return;
        }

        const claim = await getClaimDetail(editingClaimId);
        setForm({
          title: claim.title,
          description: claim.description ?? "",
          category_id: String(claim.category_id),
          original_currency: claim.original_currency,
          original_amount: String(claim.original_amount),
          expense_date: claim.expense_date,
        });
      } catch (unknownError) {
        setError(getApiErrorMessage(unknownError, "Unable to load claim form."));
      } finally {
        setIsLoading(false);
      }
    };

    void loadData();
  }, [claimId, isEditing]);

  const onFieldChange = (field: keyof ClaimFormState, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const buildPayload = (): ClaimCreateRequest | null => {
    if (!form.title.trim()) {
      setError("Title is required.");
      return null;
    }

    if (!form.category_id) {
      setError("Category is required.");
      return null;
    }

    const amount = Number(form.original_amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setError("Amount must be greater than 0.");
      return null;
    }

    if (!form.expense_date) {
      setError("Expense date is required.");
      return null;
    }

    return {
      title: form.title.trim(),
      description: form.description.trim() || null,
      category_id: Number(form.category_id),
      original_currency: form.original_currency.trim().toUpperCase(),
      original_amount: amount,
      expense_date: form.expense_date,
      department_id: null,
    };
  };

  const saveDraft = async () => {
    setError("");
    setSuccessMessage("");

    const payload = buildPayload();
    if (!payload) {
      return;
    }

    setIsSaving(true);
    try {
      if (claimId !== null) {
        await updateDraftClaim(claimId, payload);
      } else {
        const created = await createClaim(payload);
        navigate(`/employee/submit?claimId=${created.id}`, { replace: true });
      }
      setSuccessMessage("Draft saved successfully.");
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, defaultErrorMessage));
    } finally {
      setIsSaving(false);
    }
  };

  const saveAndSubmit = async () => {
    setError("");
    setSuccessMessage("");

    const payload = buildPayload();
    if (!payload) {
      return;
    }

    setIsSaving(true);
    try {
      const resolvedClaimId =
        claimId !== null
          ? (await updateDraftClaim(claimId, payload)).id
          : (await createClaim(payload)).id;

      await submitClaim(resolvedClaimId);
      navigate("/employee/claims", { replace: true });
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to submit claim."));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="centered-page">Loading claim form...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>{isEditing ? "Edit Draft Claim" : "Submit Expense"}</h2>
          <p className="muted">
            {isEditing
              ? "Update your draft and submit when ready."
              : "Create a draft first, then submit once details are final."}
          </p>
        </div>
        <Link to="/employee/claims" className="secondary-link-btn">
          Back to My Claims
        </Link>
      </div>

      <div className="claim-form-grid">
        <div>
          <label htmlFor="claimTitle">Title</label>
          <input
            id="claimTitle"
            type="text"
            value={form.title}
            onChange={(event) => onFieldChange("title", event.target.value)}
            placeholder="Client meeting travel"
          />
        </div>

        <div>
          <label htmlFor="claimCategory">Category</label>
          <select
            id="claimCategory"
            value={form.category_id}
            onChange={(event) => onFieldChange("category_id", event.target.value)}
          >
            <option value="">Select a category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="claimCurrency">Currency</label>
          <input
            id="claimCurrency"
            type="text"
            maxLength={3}
            value={form.original_currency}
            onChange={(event) => onFieldChange("original_currency", event.target.value)}
            placeholder="INR"
          />
        </div>

        <div>
          <label htmlFor="claimAmount">Amount</label>
          <input
            id="claimAmount"
            type="number"
            min="0.01"
            step="0.01"
            value={form.original_amount}
            onChange={(event) => onFieldChange("original_amount", event.target.value)}
            placeholder="0.00"
          />
        </div>

        <div>
          <label htmlFor="claimDate">Expense Date</label>
          <input
            id="claimDate"
            type="date"
            value={form.expense_date}
            onChange={(event) => onFieldChange("expense_date", event.target.value)}
          />
        </div>

        <div className="full-width">
          <label htmlFor="claimDescription">Description</label>
          <textarea
            id="claimDescription"
            className="text-area"
            value={form.description}
            onChange={(event) => onFieldChange("description", event.target.value)}
            placeholder="Add context for approvers"
          />
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {successMessage ? <p className="success-text">{successMessage}</p> : null}

      <div className="quick-actions">
        <button type="button" className="secondary-link-btn" onClick={saveDraft} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Draft"}
        </button>
        <button type="button" className="primary-link-btn" onClick={saveAndSubmit} disabled={isSaving}>
          {isSaving ? "Submitting..." : "Save & Submit"}
        </button>
      </div>
    </div>
  );
};
