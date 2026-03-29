import axios from "axios";
import { useEffect, useState } from "react";

import { createDepartment, listDepartments, updateDepartment } from "../api/admin";
import type { Department } from "../types/admin";

const getApiErrorMessage = (unknownError: unknown, fallback: string): string => {
  if (!axios.isAxiosError(unknownError)) {
    return fallback;
  }

  const detail = unknownError.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  return fallback;
};

export const AdminDepartmentsPage = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [editing, setEditing] = useState<Record<number, { name: string; code: string }>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDepartments = async () => {
    setError("");
    setIsLoading(true);

    try {
      const data = await listDepartments();
      setDepartments(data);
      setEditing(
        Object.fromEntries(
          data.map((department) => [
            department.id,
            {
              name: department.name,
              code: department.code ?? "",
            },
          ]),
        ),
      );
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load departments."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadDepartments();
  }, []);

  const onCreateDepartment = async () => {
    setError("");

    if (!newName.trim()) {
      setError("Department name is required.");
      return;
    }

    try {
      await createDepartment({
        name: newName.trim(),
        code: newCode.trim() || null,
      });
      setNewName("");
      setNewCode("");
      await loadDepartments();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to create department."));
    }
  };

  const onSaveDepartment = async (departmentId: number) => {
    setError("");
    const row = editing[departmentId];
    if (!row || !row.name.trim()) {
      setError("Department name is required.");
      return;
    }

    try {
      await updateDepartment(departmentId, {
        name: row.name.trim(),
        code: row.code.trim() || null,
      });
      await loadDepartments();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to update department."));
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Department Management</h2>
          <p className="muted">Create and update company departments.</p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="admin-form-card">
        <h3>Create Department</h3>
        <div className="admin-grid-3">
          <input
            type="text"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            placeholder="Department name"
          />
          <input
            type="text"
            value={newCode}
            onChange={(event) => setNewCode(event.target.value)}
            placeholder="Code (optional)"
          />
          <button type="button" className="primary-link-btn" onClick={() => void onCreateDepartment()}>
            Add Department
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="centered-page">Loading departments...</div>
      ) : (
        <div className="table-wrap">
          <table className="claims-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Code</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {departments.map((department) => {
                const row = editing[department.id] ?? { name: department.name, code: department.code ?? "" };
                return (
                  <tr key={department.id}>
                    <td>{department.id}</td>
                    <td>
                      <input
                        type="text"
                        value={row.name}
                        onChange={(event) =>
                          setEditing((current) => ({
                            ...current,
                            [department.id]: {
                              ...row,
                              name: event.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={row.code}
                        onChange={(event) =>
                          setEditing((current) => ({
                            ...current,
                            [department.id]: {
                              ...row,
                              code: event.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="secondary-link-btn"
                        onClick={() => void onSaveDepartment(department.id)}
                      >
                        Save
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
