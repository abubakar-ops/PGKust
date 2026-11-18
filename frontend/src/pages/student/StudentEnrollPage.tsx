import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { getAvailableAllocations, enroll } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { AvailableAllocation } from "../../types";

export default function StudentEnrollPage() {
  const [allocations, setAllocations] = useState<AvailableAllocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [enrollingId, setEnrollingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await getAvailableAllocations();
      setAllocations(data);
    } catch {
      setError("Failed to load available courses.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleEnroll = async (allocationId: number) => {
    setEnrollingId(allocationId);
    setError("");
    setSuccess("");
    try {
      await enroll(allocationId);
      setSuccess("Enrollment request submitted. Await admin approval.");
      await load();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail ?? "Enrollment failed. Please try again.");
    } finally {
      setEnrollingId(null);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 className="fw-bold mb-0">Enroll in Courses</h4>
          <p className="text-muted small mb-0">Available course allocations for the current session</p>
        </div>
        <Link to="/student/courses" className="btn btn-outline-secondary btn-sm">My Courses →</Link>
      </div>
      <Alert type="danger" message={error} />
      <Alert type="success" message={success} />

      {allocations.length === 0 ? (
        <div className="alert alert-info">No course allocations are available for enrollment right now.</div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Lecturer</th>
                  <th>Semester</th>
                  <th>Credit Units</th>
                  <th className="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                {allocations.map((a) => (
                  <tr key={a.id}>
                    <td><code>{a.course_code}</code></td>
                    <td>{a.course_title}</td>
                    <td>{a.lecturer_name}</td>
                    <td>{a.semester}</td>
                    <td>{a.credit_units}</td>
                    <td className="text-end">
                      <button
                        className="btn btn-sm btn-primary"
                        disabled={a.already_enrolled || enrollingId === a.id}
                        onClick={() => void handleEnroll(a.id)}
                      >
                        {a.already_enrolled ? "Enrolled" : enrollingId === a.id ? "…" : "Enroll"}
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
