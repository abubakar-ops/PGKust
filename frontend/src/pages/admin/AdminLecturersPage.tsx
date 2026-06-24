import { useState, useEffect, useCallback } from "react";
import { getPendingLecturers, approveLecturer, updateLecturer } from "../../api/auth";
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

export default function AdminLecturersPage() {
  const [lecturers, setLecturers] = useState<LecturerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actingId, setActingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await getPendingLecturers();
      setLecturers(data);
    } catch {
      setError("Could not load pending lecturers.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleAction = async (pk: number, action: "approve" | "reject") => {
    setActingId(pk);
    setError("");
    try {
      await approveLecturer(pk, action);
      setLecturers((prev) => prev.filter((l) => l.id !== pk));
    } catch {
      setError("Action failed. Please try again.");
    } finally {
      setActingId(null);
    }
  };

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
      <h4 className="fw-bold mb-1">Pending Lecturers</h4>
      <p className="text-muted">Review, edit, and approve lecturer registrations</p>
      <Alert message={error} />

      {lecturers.length === 0 ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body text-center text-muted py-5">No pending lecturer registrations.</div>
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
                  <th>Supervisor?</th>
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
                            <input type="checkbox" className="form-check-input"
                              checked={editForm.is_supervisor}
                              onChange={(e) => setEditForm({ ...editForm, is_supervisor: e.target.checked })} />
                          </td>
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
                          <td>{l.specialization || "—"}</td>
                          <td>{l.is_supervisor ? "Yes" : "No"}</td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => startEdit(l)}>
                              Edit
                            </button>
                            <button
                              className="btn btn-sm btn-success me-2"
                              disabled={actingId === l.id}
                              onClick={() => void handleAction(l.id, "approve")}
                            >
                              {actingId === l.id ? "…" : "Approve"}
                            </button>
                            <button
                              className="btn btn-sm btn-outline-danger"
                              disabled={actingId === l.id}
                              onClick={() => void handleAction(l.id, "reject")}
                            >
                              {actingId === l.id ? "…" : "Reject"}
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
