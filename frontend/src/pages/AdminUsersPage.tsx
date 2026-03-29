import axios from "axios";
import { useEffect, useMemo, useState } from "react";

import {
  createUser,
  listDepartments,
  listUsers,
  updateUser,
} from "../api/admin";
import { useAuth } from "../context/AuthContext";
import type { AdminUser, Department } from "../types/admin";
import type { UserRole } from "../types/auth";

interface CreateUserFormState {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_approver: boolean;
  department_id: string;
  manager_id: string;
}

interface EditableUserRow {
  first_name: string;
  last_name: string;
  role: UserRole;
  is_approver: boolean;
  is_active: boolean;
  department_id: string;
  manager_id: string;
  password: string;
}

const EMPTY_CREATE_FORM: CreateUserFormState = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  role: "EMPLOYEE",
  is_approver: false,
  department_id: "",
  manager_id: "",
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
    const first = detail[0] as { msg?: string };
    if (typeof first?.msg === "string" && first.msg.trim()) {
      return first.msg;
    }
  }

  return fallback;
};

const toNullableNumber = (value: string): number | null => {
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const buildEditableRows = (users: AdminUser[]): Record<number, EditableUserRow> =>
  Object.fromEntries(
    users.map((user) => [
      user.id,
      {
        first_name: user.first_name,
        last_name: user.last_name,
        role: user.role,
        is_approver: user.is_approver,
        is_active: user.is_active,
        department_id: user.department_id ? String(user.department_id) : "",
        manager_id: user.manager_id ? String(user.manager_id) : "",
        password: "",
      },
    ]),
  );

export const AdminUsersPage = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [createForm, setCreateForm] = useState<CreateUserFormState>(EMPTY_CREATE_FORM);
  const [editingRows, setEditingRows] = useState<Record<number, EditableUserRow>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const departmentById = useMemo(() => {
    return Object.fromEntries(departments.map((department) => [department.id, department]));
  }, [departments]);

  const loadUsersAndDepartments = async () => {
    setError("");
    setIsLoading(true);

    try {
      const [usersData, departmentsData] = await Promise.all([listUsers(), listDepartments()]);
      setUsers(usersData);
      setDepartments(departmentsData);
      setEditingRows(buildEditableRows(usersData));
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load users data."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadUsersAndDepartments();
  }, []);

  const onCreateUser = async () => {
    setError("");
    setSuccessMessage("");

    if (!createForm.email.trim() || !createForm.password || !createForm.first_name.trim() || !createForm.last_name.trim()) {
      setError("Email, password, first name, and last name are required.");
      return;
    }

    if (createForm.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSaving(true);
    try {
      await createUser({
        email: createForm.email.trim(),
        password: createForm.password,
        first_name: createForm.first_name.trim(),
        last_name: createForm.last_name.trim(),
        role: createForm.role,
        is_approver: createForm.is_approver,
        department_id: toNullableNumber(createForm.department_id),
        manager_id: toNullableNumber(createForm.manager_id),
      });
      setCreateForm(EMPTY_CREATE_FORM);
      await loadUsersAndDepartments();
      setSuccessMessage("User created successfully.");
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to create user."));
    } finally {
      setIsSaving(false);
    }
  };

  const onSaveUser = async (userId: number) => {
    setError("");
    setSuccessMessage("");
    const row = editingRows[userId];
    if (!row) {
      return;
    }

    if (currentUser?.id === userId && row.is_active === false) {
      setError("You cannot deactivate your own admin account.");
      return;
    }

    if (!row.first_name.trim() || !row.last_name.trim()) {
      setError("First name and last name are required.");
      return;
    }

    if (row.password && row.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSaving(true);
    try {
      await updateUser(userId, {
        first_name: row.first_name.trim(),
        last_name: row.last_name.trim(),
        role: row.role,
        is_approver: row.is_approver,
        is_active: row.is_active,
        department_id: toNullableNumber(row.department_id),
        manager_id: toNullableNumber(row.manager_id),
        ...(row.password ? { password: row.password } : {}),
      });
      await loadUsersAndDepartments();
      setSuccessMessage("User updated successfully.");
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to update user."));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>User Management</h2>
          <p className="muted">Create users, assign managers/departments, and adjust permissions.</p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {successMessage ? <p className="success-text">{successMessage}</p> : null}

      <div className="admin-form-card">
        <h3>Create User</h3>
        <div className="admin-grid-4">
          <input
            type="email"
            value={createForm.email}
            onChange={(event) =>
              setCreateForm((current) => ({ ...current, email: event.target.value }))
            }
            placeholder="Email"
          />
          <input
            type="password"
            value={createForm.password}
            onChange={(event) =>
              setCreateForm((current) => ({ ...current, password: event.target.value }))
            }
            placeholder="Password"
          />
          <input
            type="text"
            value={createForm.first_name}
            onChange={(event) =>
              setCreateForm((current) => ({ ...current, first_name: event.target.value }))
            }
            placeholder="First name"
          />
          <input
            type="text"
            value={createForm.last_name}
            onChange={(event) =>
              setCreateForm((current) => ({ ...current, last_name: event.target.value }))
            }
            placeholder="Last name"
          />
          <select
            value={createForm.role}
            onChange={(event) =>
              setCreateForm((current) => ({
                ...current,
                role: event.target.value as UserRole,
              }))
            }
          >
            <option value="EMPLOYEE">EMPLOYEE</option>
            <option value="ADMIN">ADMIN</option>
          </select>
          <label className="inline-checkbox">
            <input
              type="checkbox"
              checked={createForm.is_approver}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  is_approver: event.target.checked,
                }))
              }
            />
            Approver
          </label>
          <select
            value={createForm.department_id}
            onChange={(event) =>
              setCreateForm((current) => ({
                ...current,
                department_id: event.target.value,
              }))
            }
          >
            <option value="">Department: none</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </select>
          <select
            value={createForm.manager_id}
            onChange={(event) =>
              setCreateForm((current) => ({
                ...current,
                manager_id: event.target.value,
              }))
            }
          >
            <option value="">Manager: none</option>
            {users
              .filter((candidate) => candidate.is_active)
              .map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.first_name} {candidate.last_name} ({candidate.email})
                </option>
              ))}
          </select>
        </div>
        <div className="quick-actions">
          <button
            type="button"
            className="primary-link-btn"
            onClick={() => void onCreateUser()}
            disabled={isSaving}
          >
            {isSaving ? "Saving..." : "Add User"}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="centered-page">Loading users...</div>
      ) : (
        <div className="table-wrap">
          <table className="claims-table users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Role</th>
                <th>Approver</th>
                <th>Active</th>
                <th>Department</th>
                <th>Manager</th>
                <th>Password Reset</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => {
                const row = editingRows[user.id];
                if (!row) {
                  return null;
                }

                return (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.email}</td>
                    <td>
                      <input
                        type="text"
                        value={row.first_name}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              first_name: event.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={row.last_name}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              last_name: event.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <select
                        value={row.role}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              role: event.target.value as UserRole,
                            },
                          }))
                        }
                      >
                        <option value="EMPLOYEE">EMPLOYEE</option>
                        <option value="ADMIN">ADMIN</option>
                      </select>
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={row.is_approver}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              is_approver: event.target.checked,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={row.is_active}
                        disabled={currentUser?.id === user.id}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              is_active: event.target.checked,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <select
                        value={row.department_id}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              department_id: event.target.value,
                            },
                          }))
                        }
                      >
                        <option value="">None</option>
                        {departments.map((department) => (
                          <option key={department.id} value={department.id}>
                            {department.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <select
                        value={row.manager_id}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              manager_id: event.target.value,
                            },
                          }))
                        }
                      >
                        <option value="">None</option>
                        {users
                          .filter((candidate) => candidate.id !== user.id && candidate.is_active)
                          .map((candidate) => (
                            <option key={candidate.id} value={candidate.id}>
                              {candidate.first_name} {candidate.last_name}
                            </option>
                          ))}
                      </select>
                    </td>
                    <td>
                      <input
                        type="password"
                        value={row.password}
                        onChange={(event) =>
                          setEditingRows((current) => ({
                            ...current,
                            [user.id]: {
                              ...row,
                              password: event.target.value,
                            },
                          }))
                        }
                        placeholder="Optional"
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="secondary-link-btn"
                        disabled={isSaving}
                        onClick={() => void onSaveUser(user.id)}
                      >
                        {isSaving ? "Saving..." : "Save"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!isLoading && users.length === 0 ? <p className="muted">No users found.</p> : null}
      {!isLoading && departments.length === 0 ? (
        <p className="muted">No departments configured yet; users can still be created without one.</p>
      ) : null}
      {!isLoading && users.length > 0 ? (
        <p className="muted">
          Editing notes: leave password blank to keep it unchanged. Department codes are shown in{' '}
          {Object.values(departmentById).length > 0 ? "department pages" : "department setup"}.
        </p>
      ) : null}
    </div>
  );
};
