import { useState, useEffect, useCallback } from "react";
import { getAllLecturers, updateLecturer } from "../../api/auth";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { LecturerProfile } from "../../types";

interface EditForm {
  first_name: string;
  last_name: string;
  staff_id: string;
  specialization: string;
  is_supervisor: boolean;
}

export default function AdminAllLecturersPage() {
  const [lecturers, setLecturers] = useState<LecturerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await getAllLecturers(statusFilter || undefined);
      setLecturers(data);
    } catch {
      setError("Could not load lecturers.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { void load(); }, [load]);

  const startEdit = (l: LecturerProfile) => {
    setEditingId(l.id);
    setEditForm({
      first_name: l.first_name,
      last_name: l.last_name,
      staff_id: l.staff_id,
      specialization: l.specialization,
      is_supervisor: l.is_supervisor,
    });
    setError("");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm(null);
  };

  const saveEdit = async (pk: number) => {
    if (!editForm) return;
    setSaving(true);
    setError("");
    try {
      const { data } = await updateLecturer(pk, editForm);
      setLecturers((prev) => prev.map((l) => (l.id === pk ? data : l)));
      cancelEdit();
    } catch {
      setError("Could not save changes. Check the fields and try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1 text-white">All Lecturers</h4>
      <p className="text-white">View and edit all registered lecturers, regardless of status</p>
      <Alert message={error} />

      <div className="mb-3" style={{ maxWidth: 220 }}>
        <select
          className="form-select form-select-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="ACTIVE">Active</option>
        </select>
      </div>

      {lecturers.length === 0 ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body text-center text-muted py-5">No lecturers found.</div>
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Staff ID</th>
                  <th>Specialization</th>
                  <th>Supervisor</th>
                  <th>Status</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {lecturers.map((l) => {
                  const isEditing = editingId === l.id;
                  return (
                    <tr key={l.id}>
                      {isEditing && editForm ? (
                        <>
                          <td className="d-flex gap-1">
                            <input className="form-control form-control-sm" style={{ width: 100 }}
                              value={editForm.first_name}
                              onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })} />
                            <input className="form-control form-control-sm" style={{ width: 100 }}
                              value={editForm.last_name}
                              onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })} />
                          </td>
                          <td>{l.email}</td>
                          <td>
                            <input className="form-control form-control-sm"
                              value={editForm.staff_id}
                              onChange={(e) => setEditForm({ ...editForm, staff_id: e.target.value })} />
                          </td>
                          <td>
                            <input className="form-control form-control-sm"
                              value={editForm.specialization}
                              onChange={(e) => setEditForm({ ...editForm, specialization: e.target.value })} />
                          </td>
                          <td>
                            <input type="checkbox"
                              checked={editForm.is_supervisor}
                              onChange={(e) => setEditForm({ ...editForm, is_supervisor: e.target.checked })} />
                          </td>
                          <td>{l.status}</td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-primary me-2" disabled={saving}
                              onClick={() => void saveEdit(l.id)}>
                              {saving ? "…" : "Save"}
                            </button>
                            <button className="btn btn-sm btn-outline-secondary" disabled={saving} onClick={cancelEdit}>
                              Cancel
                            </button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{l.full_name}</td>
                          <td>{l.email}</td>
                          <td>{l.staff_id}</td>
                          <td>{l.specialization}</td>
                          <td>{l.is_supervisor ? "Yes" : "No"}</td>
                          <td>
                            <span className={`badge ${l.status === "ACTIVE" ? "bg-success" : "bg-secondary"}`}>
                              {l.status}
                            </span>
                          </td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-outline-secondary" onClick={() => startEdit(l)}>
                              Edit
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
