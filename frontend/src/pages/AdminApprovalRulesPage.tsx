import axios from "axios";
import { useEffect, useMemo, useState } from "react";

import {
  createApprovalRule,
  listApprovalRules,
  replaceApprovalRuleSteps,
  updateApprovalRule,
} from "../api/approvalRules";
import { listCategories, listDepartments, listUsers } from "../api/admin";
import type { Category, Department, AdminUser } from "../types/admin";
import type {
  ApprovalRule,
  ApprovalRuleCreatePayload,
  ApprovalRuleStepPayload,
  ApprovalRuleStrategy,
  StepApproverRole,
} from "../types/approvalRules";

interface RuleFormState {
  name: string;
  description: string;
  min_amount: string;
  max_amount: string;
  category_id: string;
  department_id: string;
  strategy: ApprovalRuleStrategy;
  min_approval_percentage: string;
  priority: string;
  is_active: boolean;
}

interface StepFormState {
  step_order: string;
  name: string;
  approver_role: StepApproverRole;
  approver_user_id: string;
  approver_department_id: string;
}

const EMPTY_RULE_FORM: RuleFormState = {
  name: "",
  description: "",
  min_amount: "",
  max_amount: "",
  category_id: "",
  department_id: "",
  strategy: "SEQUENTIAL",
  min_approval_percentage: "",
  priority: "100",
  is_active: true,
};

const createEmptyStep = (stepOrder: number): StepFormState => ({
  step_order: String(stepOrder),
  name: "",
  approver_role: "MANAGER",
  approver_user_id: "",
  approver_department_id: "",
});

const getApiErrorMessage = (unknownError: unknown, fallback: string): string => {
  if (!axios.isAxiosError(unknownError)) {
    return fallback;
  }

  const detail = unknownError.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    if (typeof first?.msg === "string" && first.msg.trim()) {
      return first.msg;
    }
  }

  return fallback;
};

const toNullableNumber = (value: string): number | null => {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const ruleToFormState = (rule: ApprovalRule): RuleFormState => ({
  name: rule.name,
  description: rule.description ?? "",
  min_amount: rule.min_amount === null ? "" : String(rule.min_amount),
  max_amount: rule.max_amount === null ? "" : String(rule.max_amount),
  category_id: rule.category_id === null ? "" : String(rule.category_id),
  department_id: rule.department_id === null ? "" : String(rule.department_id),
  strategy: rule.strategy,
  min_approval_percentage:
    rule.min_approval_percentage === null ? "" : String(rule.min_approval_percentage),
  priority: String(rule.priority),
  is_active: rule.is_active,
});

const stepsToFormState = (rule: ApprovalRule): StepFormState[] =>
  [...rule.steps]
    .sort((a, b) => a.step_order - b.step_order)
    .map((step) => ({
      step_order: String(step.step_order),
      name: step.name,
      approver_role: step.approver_role,
      approver_user_id: step.approver_user_id === null ? "" : String(step.approver_user_id),
      approver_department_id:
        step.approver_department_id === null ? "" : String(step.approver_department_id),
    }));

export const AdminApprovalRulesPage = () => {
  const [rules, setRules] = useState<ApprovalRule[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null);
  const [createForm, setCreateForm] = useState<RuleFormState>(EMPTY_RULE_FORM);
  const [createSteps, setCreateSteps] = useState<StepFormState[]>([createEmptyStep(1)]);
  const [editForm, setEditForm] = useState<RuleFormState>(EMPTY_RULE_FORM);
  const [editSteps, setEditSteps] = useState<StepFormState[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const selectedRule = useMemo(
    () => rules.find((rule) => rule.id === selectedRuleId) ?? null,
    [rules, selectedRuleId],
  );

  const approverUsers = useMemo(
    () => users.filter((user) => user.is_active && (user.is_approver || user.role === "ADMIN")),
    [users],
  );

  const loadData = async () => {
    setError("");
    setIsLoading(true);

    try {
      const [rulesData, categoriesData, departmentsData, usersData] = await Promise.all([
        listApprovalRules(),
        listCategories(),
        listDepartments(),
        listUsers(),
      ]);

      setRules(rulesData);
      setCategories(categoriesData);
      setDepartments(departmentsData);
      setUsers(usersData);

      const nextRuleId = rulesData[0]?.id ?? null;
      setSelectedRuleId(nextRuleId);

      if (nextRuleId !== null) {
        const rule = rulesData.find((item) => item.id === nextRuleId);
        if (rule) {
          setEditForm(ruleToFormState(rule));
          setEditSteps(stepsToFormState(rule));
        }
      } else {
        setEditForm(EMPTY_RULE_FORM);
        setEditSteps([]);
      }
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load approval rules."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const onSelectRule = (ruleId: number) => {
    const rule = rules.find((item) => item.id === ruleId);
    if (!rule) {
      return;
    }

    setSelectedRuleId(ruleId);
    setEditForm(ruleToFormState(rule));
    setEditSteps(stepsToFormState(rule));
    setError("");
    setSuccessMessage("");
  };

  const buildRulePayload = (
    form: RuleFormState,
    steps: StepFormState[],
  ): ApprovalRuleCreatePayload | null => {
    if (!form.name.trim()) {
      setError("Rule name is required.");
      return null;
    }

    const priority = Number(form.priority);
    if (!Number.isFinite(priority) || priority < 1) {
      setError("Priority must be a positive number.");
      return null;
    }

    const minApprovalPercentage =
      form.strategy === "MIN_APPROVALS" ? toNullableNumber(form.min_approval_percentage) : null;

    if (form.strategy === "MIN_APPROVALS" && minApprovalPercentage === null) {
      setError("min approval percentage is required for MIN_APPROVALS strategy.");
      return null;
    }

    const stepPayload: ApprovalRuleStepPayload[] = [];
    for (const step of steps) {
      const stepOrder = Number(step.step_order);
      if (!Number.isFinite(stepOrder) || stepOrder < 1) {
        setError("Each step must have a valid step order.");
        return null;
      }
      if (!step.name.trim()) {
        setError("Each step must have a name.");
        return null;
      }

      stepPayload.push({
        step_order: stepOrder,
        name: step.name.trim(),
        approver_role: step.approver_role,
        approver_user_id:
          step.approver_role === "SPECIFIC_USER" ? toNullableNumber(step.approver_user_id) : null,
        approver_department_id:
          step.approver_role === "DEPARTMENT_HEAD"
            ? toNullableNumber(step.approver_department_id)
            : null,
      });
    }

    if (stepPayload.length === 0) {
      setError("At least one step is required.");
      return null;
    }

    return {
      name: form.name.trim(),
      description: form.description.trim() || null,
      min_amount: toNullableNumber(form.min_amount),
      max_amount: toNullableNumber(form.max_amount),
      category_id: toNullableNumber(form.category_id),
      department_id: toNullableNumber(form.department_id),
      strategy: form.strategy,
      min_approval_percentage: minApprovalPercentage,
      is_active: form.is_active,
      priority,
      steps: stepPayload,
    };
  };

  const onCreateRule = async () => {
    setError("");
    setSuccessMessage("");

    const payload = buildRulePayload(createForm, createSteps);
    if (!payload) {
      return;
    }

    setIsSaving(true);
    try {
      const created = await createApprovalRule(payload);
      await loadData();
      setSelectedRuleId(created.id);
      setCreateForm(EMPTY_RULE_FORM);
      setCreateSteps([createEmptyStep(1)]);
      setSuccessMessage("Approval rule created successfully.");
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to create approval rule."));
    } finally {
      setIsSaving(false);
    }
  };

  const onSaveRuleMeta = async () => {
    if (!selectedRule) {
      return;
    }

    setError("");
    setSuccessMessage("");

    const payload = buildRulePayload(editForm, editSteps);
    if (!payload) {
      return;
    }

    setIsSaving(true);
    try {
      await updateApprovalRule(selectedRule.id, {
        name: payload.name,
        description: payload.description,
        min_amount: payload.min_amount,
        max_amount: payload.max_amount,
        category_id: payload.category_id,
        department_id: payload.department_id,
        strategy: payload.strategy,
        min_approval_percentage: payload.min_approval_percentage,
        is_active: payload.is_active,
        priority: payload.priority,
      });
      await loadData();
      setSelectedRuleId(selectedRule.id);
      setSuccessMessage("Rule settings saved.");
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to update rule."));
    } finally {
      setIsSaving(false);
    }
  };

  const onSaveRuleSteps = async () => {
    if (!selectedRule) {
      return;
    }

    setError("");
    setSuccessMessage("");

    const payload = buildRulePayload(editForm, editSteps);
    if (!payload) {
      return;
    }

    setIsSaving(true);
    try {
      await replaceApprovalRuleSteps(selectedRule.id, payload.steps);
      await loadData();
      setSelectedRuleId(selectedRule.id);
      setSuccessMessage("Rule steps saved.");
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to update rule steps."));
    } finally {
      setIsSaving(false);
    }
  };

  const addCreateStep = () => {
    setCreateSteps((current) => [...current, createEmptyStep(current.length + 1)]);
  };

  const addEditStep = () => {
    setEditSteps((current) => [...current, createEmptyStep(current.length + 1)]);
  };

  const removeCreateStep = (index: number) => {
    setCreateSteps((current) => current.filter((_, idx) => idx !== index));
  };

  const removeEditStep = (index: number) => {
    setEditSteps((current) => current.filter((_, idx) => idx !== index));
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Approval Rule Management</h2>
          <p className="muted">Configure matching criteria, strategy, and multi-step approver routing.</p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {successMessage ? <p className="success-text">{successMessage}</p> : null}

      <div className="admin-form-card">
        <h3>Create Rule</h3>
        <RuleMetaForm
          form={createForm}
          onChange={setCreateForm}
          categories={categories}
          departments={departments}
        />
        <StepEditor
          steps={createSteps}
          setSteps={setCreateSteps}
          users={approverUsers}
          departments={departments}
          onAddStep={addCreateStep}
          onRemoveStep={removeCreateStep}
        />
        <div className="quick-actions">
          <button type="button" className="primary-link-btn" onClick={() => void onCreateRule()} disabled={isSaving}>
            {isSaving ? "Saving..." : "Create Rule"}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="centered-page">Loading approval rules...</div>
      ) : (
        <div className="rules-layout">
          <aside className="rules-list">
            <h3>Configured Rules</h3>
            {rules.length === 0 ? <p className="muted">No rules yet.</p> : null}
            {rules.map((rule) => (
              <button
                key={rule.id}
                type="button"
                className={
                  selectedRuleId === rule.id
                    ? "approval-task-button approval-task-button-active"
                    : "approval-task-button"
                }
                onClick={() => onSelectRule(rule.id)}
              >
                <strong>{rule.name}</strong>
                <span className="muted">Priority {rule.priority}</span>
                <span>{rule.strategy}</span>
              </button>
            ))}
          </aside>

          <section className="rules-detail">
            {selectedRule ? (
              <>
                <h3>Edit Rule: {selectedRule.name}</h3>
                <RuleMetaForm
                  form={editForm}
                  onChange={setEditForm}
                  categories={categories}
                  departments={departments}
                />
                <div className="quick-actions">
                  <button
                    type="button"
                    className="secondary-link-btn"
                    onClick={() => void onSaveRuleMeta()}
                    disabled={isSaving}
                  >
                    {isSaving ? "Saving..." : "Save Rule Settings"}
                  </button>
                </div>

                <StepEditor
                  steps={editSteps}
                  setSteps={setEditSteps}
                  users={approverUsers}
                  departments={departments}
                  onAddStep={addEditStep}
                  onRemoveStep={removeEditStep}
                />
                <div className="quick-actions">
                  <button
                    type="button"
                    className="primary-link-btn"
                    onClick={() => void onSaveRuleSteps()}
                    disabled={isSaving}
                  >
                    {isSaving ? "Saving..." : "Save Rule Steps"}
                  </button>
                </div>
              </>
            ) : (
              <p className="muted">Select a rule to edit.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
};

const RuleMetaForm = ({
  form,
  onChange,
  categories,
  departments,
}: {
  form: RuleFormState;
  onChange: (next: RuleFormState | ((current: RuleFormState) => RuleFormState)) => void;
  categories: Category[];
  departments: Department[];
}) => (
  <div className="admin-grid-4">
    <input
      type="text"
      value={form.name}
      onChange={(event) => onChange((current) => ({ ...current, name: event.target.value }))}
      placeholder="Rule name"
    />
    <input
      type="text"
      value={form.description}
      onChange={(event) => onChange((current) => ({ ...current, description: event.target.value }))}
      placeholder="Description"
    />
    <input
      type="number"
      min={0}
      step="0.01"
      value={form.min_amount}
      onChange={(event) => onChange((current) => ({ ...current, min_amount: event.target.value }))}
      placeholder="Min amount"
    />
    <input
      type="number"
      min={0}
      step="0.01"
      value={form.max_amount}
      onChange={(event) => onChange((current) => ({ ...current, max_amount: event.target.value }))}
      placeholder="Max amount"
    />
    <select
      value={form.category_id}
      onChange={(event) => onChange((current) => ({ ...current, category_id: event.target.value }))}
    >
      <option value="">Category: any</option>
      {categories.map((category) => (
        <option key={category.id} value={category.id}>
          {category.name}
        </option>
      ))}
    </select>
    <select
      value={form.department_id}
      onChange={(event) => onChange((current) => ({ ...current, department_id: event.target.value }))}
    >
      <option value="">Department: any</option>
      {departments.map((department) => (
        <option key={department.id} value={department.id}>
          {department.name}
        </option>
      ))}
    </select>
    <select
      value={form.strategy}
      onChange={(event) =>
        onChange((current) => ({
          ...current,
          strategy: event.target.value as ApprovalRuleStrategy,
          min_approval_percentage:
            event.target.value === "MIN_APPROVALS" ? current.min_approval_percentage : "",
        }))
      }
    >
      <option value="SEQUENTIAL">SEQUENTIAL</option>
      <option value="MIN_APPROVALS">MIN_APPROVALS</option>
    </select>
    <input
      type="number"
      min={1}
      max={100}
      value={form.min_approval_percentage}
      onChange={(event) =>
        onChange((current) => ({ ...current, min_approval_percentage: event.target.value }))
      }
      placeholder="Min approval %"
      disabled={form.strategy !== "MIN_APPROVALS"}
    />
    <input
      type="number"
      min={1}
      value={form.priority}
      onChange={(event) => onChange((current) => ({ ...current, priority: event.target.value }))}
      placeholder="Priority"
    />
    <label className="inline-checkbox">
      <input
        type="checkbox"
        checked={form.is_active}
        onChange={(event) => onChange((current) => ({ ...current, is_active: event.target.checked }))}
      />
      Active rule
    </label>
  </div>
);

const StepEditor = ({
  steps,
  setSteps,
  users,
  departments,
  onAddStep,
  onRemoveStep,
}: {
  steps: StepFormState[];
  setSteps: (next: StepFormState[] | ((current: StepFormState[]) => StepFormState[])) => void;
  users: AdminUser[];
  departments: Department[];
  onAddStep: () => void;
  onRemoveStep: (index: number) => void;
}) => (
  <div className="rule-steps-editor">
    <h4>Rule Steps</h4>
    {steps.map((step, index) => (
      <div key={`${step.step_order}-${index}`} className="rule-step-row">
        <input
          type="number"
          min={1}
          value={step.step_order}
          onChange={(event) =>
            setSteps((current) =>
              current.map((item, idx) =>
                idx === index ? { ...item, step_order: event.target.value } : item,
              ),
            )
          }
          placeholder="Order"
        />
        <input
          type="text"
          value={step.name}
          onChange={(event) =>
            setSteps((current) =>
              current.map((item, idx) =>
                idx === index ? { ...item, name: event.target.value } : item,
              ),
            )
          }
          placeholder="Step name"
        />
        <select
          value={step.approver_role}
          onChange={(event) =>
            setSteps((current) =>
              current.map((item, idx) =>
                idx === index
                  ? {
                      ...item,
                      approver_role: event.target.value as StepApproverRole,
                      approver_user_id: "",
                      approver_department_id: "",
                    }
                  : item,
              ),
            )
          }
        >
          <option value="MANAGER">MANAGER</option>
          <option value="SPECIFIC_USER">SPECIFIC_USER</option>
          <option value="DEPARTMENT_HEAD">DEPARTMENT_HEAD</option>
        </select>
        <select
          value={step.approver_user_id}
          onChange={(event) =>
            setSteps((current) =>
              current.map((item, idx) =>
                idx === index ? { ...item, approver_user_id: event.target.value } : item,
              ),
            )
          }
          disabled={step.approver_role !== "SPECIFIC_USER"}
        >
          <option value="">Approver user</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.first_name} {user.last_name}
            </option>
          ))}
        </select>
        <select
          value={step.approver_department_id}
          onChange={(event) =>
            setSteps((current) =>
              current.map((item, idx) =>
                idx === index ? { ...item, approver_department_id: event.target.value } : item,
              ),
            )
          }
          disabled={step.approver_role !== "DEPARTMENT_HEAD"}
        >
          <option value="">Approver department</option>
          {departments.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
            </option>
          ))}
        </select>
        <button type="button" className="secondary-link-btn" onClick={() => onRemoveStep(index)}>
          Remove
        </button>
      </div>
    ))}
    <div className="quick-actions">
      <button type="button" className="secondary-link-btn" onClick={onAddStep}>
        Add Step
      </button>
    </div>
  </div>
);
