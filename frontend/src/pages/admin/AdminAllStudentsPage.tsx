import { useState, useEffect, useCallback } from "react";
import { getAllLecturers, getAllStudents, updateStudent, changeStudentStatus } from "../../api/auth";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { LecturerProfile, StudentProfile, ProgrammeType } from "../../types";

interface EditForm {
  first_name: string;
  last_name: string;
  matric_number: string;
  programme: ProgrammeType;
  admission_year: number;
  supervisor: number | null;
}

export default function AdminAllStudentsPage() {
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [supervisors, setSupervisors] = useState<LecturerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [actingId, setActingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [studentsResponse, lecturersResponse] = await Promise.all([
        getAllStudents(statusFilter || undefined),
        getAllLecturers("ACTIVE"),
      ]);
      setStudents(studentsResponse.data);
      setSupervisors(lecturersResponse.data.filter((lecturer) => lecturer.is_supervisor));
    } catch {
      setError("Could not load students or supervisors.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { void load(); }, [load]);

  const startEdit = (s: StudentProfile) => {
    setEditingId(s.id);
    setEditForm({
      first_name: s.first_name,
      last_name: s.last_name,
      matric_number: s.matric_number,
      programme: s.programme,
      admission_year: s.admission_year,
      supervisor: s.supervisor,
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
      const { data } = await updateStudent(pk, editForm);
      setStudents((prev) => prev.map((s) => (s.id === pk ? data : s)));
      cancelEdit();
    } catch {
      setError("Could not save changes. Check the fields and try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (s: StudentProfile, action: "reactivate" | "graduate" | "suspend") => {
    const confirmations = {
      graduate: `Mark ${s.full_name} as graduated? They will lose access to the portal.`,
      suspend: `Suspend ${s.full_name}? They will lose access to the portal.`,
      reactivate: `Reactivate ${s.full_name}?`,
    };
    if (!window.confirm(confirmations[action])) return;
    setActingId(s.id);
    setError("");
    try {
      const { data } = await changeStudentStatus(s.id, action);
      setStudents((prev) => {
        const updated = prev.map((x) => (x.id === s.id ? data : x));
        return statusFilter ? updated.filter((x) => x.status === statusFilter) : updated;
      });
    } catch {
      setError("Could not change the student's status. Please try again.");
    } finally {
      setActingId(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1 text-white">All Students</h4>
      <p className="text-white">View and edit all registered students, regardless of status</p>
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
          <option value="SUSPENDED">Suspended</option>
          <option value="GRADUATED">Graduated</option>
        </select>
      </div>

      {students.length === 0 ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body text-center text-muted py-5">No students found.</div>
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Matric No.</th>
                  <th>Programme</th>
                  <th>Supervisor</th>
                  <th>Admission Year</th>
                  <th>Status</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => {
                  const isEditing = editingId === s.id;
                  return (
                    <tr key={s.id}>
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
                          <td>{s.email}</td>
                          <td>
                            <input className="form-control form-control-sm"
                              value={editForm.matric_number}
                              onChange={(e) => setEditForm({ ...editForm, matric_number: e.target.value })} />
                          </td>
                          <td>
                            <select className="form-select form-select-sm"
                              value={editForm.programme}
                              onChange={(e) => setEditForm({ ...editForm, programme: e.target.value as ProgrammeType })}>
                              <option value="MSC">MSc</option>
                              <option value="PHD">PhD</option>
                            </select>
                          </td>
                          <td>
                            <select
                              className="form-select form-select-sm"
                              value={editForm.supervisor ?? ""}
                              onChange={(e) => setEditForm({
                                ...editForm,
                                supervisor: e.target.value ? Number(e.target.value) : null,
                              })}
                            >
                              <option value="">Unassigned</option>
                              {editForm.supervisor !== null
                                && !supervisors.some((lecturer) => lecturer.id === editForm.supervisor) && (
                                  <option value={editForm.supervisor}>
                                    {s.supervisor_name || "Current supervisor"} (currently unavailable)
                                  </option>
                                )}
                              {supervisors.map((lecturer) => (
                                <option key={lecturer.id} value={lecturer.id}>
                                  {lecturer.full_name} ({lecturer.staff_id})
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <input type="number" className="form-control form-control-sm" style={{ width: 90 }}
                              value={editForm.admission_year}
                              onChange={(e) => setEditForm({ ...editForm, admission_year: Number(e.target.value) })} />
                          </td>
                          <td>{s.status}</td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-primary me-2" disabled={saving}
                              onClick={() => void saveEdit(s.id)}>
                              {saving ? "…" : "Save"}
                            </button>
                            <button className="btn btn-sm btn-outline-secondary" disabled={saving} onClick={cancelEdit}>
                              Cancel
                            </button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{s.full_name}</td>
                          <td>{s.email}</td>
                          <td>{s.matric_number}</td>
                          <td>{s.programme}</td>
                          <td>{s.supervisor_name || "—"}</td>
                          <td>{s.admission_year}</td>
                          <td>
                            <span className={`badge ${s.status === "ACTIVE" ? "bg-success" : s.status === "SUSPENDED" ? "bg-danger" : "bg-secondary"}`}>
                              {s.status}
                            </span>
                          </td>
                          <td className="text-end">
                            <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => startEdit(s)}>
                              Edit
                            </button>
                            {s.status === "ACTIVE" && (
                              <>
                                <button className="btn btn-sm btn-outline-primary me-2" disabled={actingId === s.id}
                                  onClick={() => void handleStatusChange(s, "graduate")}>
                                  Graduate
                                </button>
                                <button className="btn btn-sm btn-outline-danger" disabled={actingId === s.id}
                                  onClick={() => void handleStatusChange(s, "suspend")}>
                                  Suspend
                                </button>
                              </>
                            )}
                            {(s.status === "SUSPENDED" || s.status === "GRADUATED") && (
                              <button className="btn btn-sm btn-success" disabled={actingId === s.id}
                                onClick={() => void handleStatusChange(s, "reactivate")}>
                                Reactivate
                              </button>
                            )}
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
