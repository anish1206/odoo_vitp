import axios from "axios";
import { useEffect, useState } from "react";

import { createCategory, listCategories, updateCategory } from "../api/admin";
import type { Category } from "../types/admin";

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

export const AdminCategoriesPage = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [editing, setEditing] = useState<
    Record<number, { name: string; code: string; description: string; is_active: boolean }>
  >({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadCategories = async () => {
    setError("");
    setIsLoading(true);

    try {
      const data = await listCategories();
      setCategories(data);
      setEditing(
        Object.fromEntries(
          data.map((category) => [
            category.id,
            {
              name: category.name,
              code: category.code ?? "",
              description: category.description ?? "",
              is_active: category.is_active,
            },
          ]),
        ),
      );
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to load categories."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadCategories();
  }, []);

  const onCreateCategory = async () => {
    setError("");

    if (!newName.trim()) {
      setError("Category name is required.");
      return;
    }

    try {
      await createCategory({
        name: newName.trim(),
        code: newCode.trim() || null,
        description: newDescription.trim() || null,
      });
      setNewName("");
      setNewCode("");
      setNewDescription("");
      await loadCategories();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to create category."));
    }
  };

  const onSaveCategory = async (categoryId: number) => {
    setError("");
    const row = editing[categoryId];
    if (!row || !row.name.trim()) {
      setError("Category name is required.");
      return;
    }

    try {
      await updateCategory(categoryId, {
        name: row.name.trim(),
        code: row.code.trim() || null,
        description: row.description.trim() || null,
        is_active: row.is_active,
      });
      await loadCategories();
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError, "Unable to update category."));
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Category Management</h2>
          <p className="muted">Manage reimbursable expense categories.</p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="admin-form-card">
        <h3>Create Category</h3>
        <div className="admin-grid-3">
          <input
            type="text"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            placeholder="Category name"
          />
          <input
            type="text"
            value={newCode}
            onChange={(event) => setNewCode(event.target.value)}
            placeholder="Code (optional)"
          />
          <input
            type="text"
            value={newDescription}
            onChange={(event) => setNewDescription(event.target.value)}
            placeholder="Description (optional)"
          />
        </div>
        <div className="quick-actions">
          <button type="button" className="primary-link-btn" onClick={() => void onCreateCategory()}>
            Add Category
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="centered-page">Loading categories...</div>
      ) : (
        <div className="table-wrap">
          <table className="claims-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Code</th>
                <th>Description</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((category) => {
                const row = editing[category.id] ?? {
                  name: category.name,
                  code: category.code ?? "",
                  description: category.description ?? "",
                  is_active: category.is_active,
                };
                return (
                  <tr key={category.id}>
                    <td>{category.id}</td>
                    <td>
                      <input
                        type="text"
                        value={row.name}
                        onChange={(event) =>
                          setEditing((current) => ({
                            ...current,
                            [category.id]: {
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
                            [category.id]: {
                              ...row,
                              code: event.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={row.description}
                        onChange={(event) =>
                          setEditing((current) => ({
                            ...current,
                            [category.id]: {
                              ...row,
                              description: event.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={row.is_active}
                        onChange={(event) =>
                          setEditing((current) => ({
                            ...current,
                            [category.id]: {
                              ...row,
                              is_active: event.target.checked,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="secondary-link-btn"
                        onClick={() => void onSaveCategory(category.id)}
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
