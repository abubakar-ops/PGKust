import { useState, useEffect, useCallback } from "react";
import { adminPendingEnrollments, adminApproveEnrollment } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { Enrollment } from "../../types";

export default function AdminEnrollmentsPage() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [actingId, setActingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await adminPendingEnrollments();
      setEnrollments(data);
    } catch {
      setError("Failed to load pending enrollments.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleAction = async (pk: number, action: "approve" | "reject") => {
    setActingId(pk);
    setError("");
    setSuccess("");
    try {
      await adminApproveEnrollment(pk, action);
      setSuccess(action === "approve" ? "Enrollment approved." : "Enrollment rejected.");
      setEnrollments((prev) => prev.filter((e) => e.id !== pk));
    } catch {
      setError("Action failed. Please try again.");
    } finally {
      setActingId(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1">Pending Enrollments</h4>
      <p className="text-muted">Review and approve student course enrollment requests</p>
      <Alert type="danger" message={error} />
      <Alert type="success" message={success} />

      {enrollments.length === 0 ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body text-center text-muted py-5">No pending enrollments.</div>
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Student</th>
                  <th>Course</th>
                  <th>Lecturer</th>
                  <th>Credit Units</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {enrollments.map((e) => (
                  <tr key={e.id}>
                    <td>{e.student_name} <span className="text-muted small">({e.matric_number})</span></td>
                    <td><code>{e.course_code}</code> {e.course_title}</td>
                    <td>{e.lecturer_name}</td>
                    <td>{e.credit_units}</td>
                    <td className="text-end">
                      <button
                        className="btn btn-sm btn-success me-2"
                        disabled={actingId === e.id}
                        onClick={() => void handleAction(e.id, "approve")}
                      >
                        {actingId === e.id ? "…" : "Approve"}
                      </button>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        disabled={actingId === e.id}
                        onClick={() => void handleAction(e.id, "reject")}
                      >
                        {actingId === e.id ? "…" : "Reject"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
