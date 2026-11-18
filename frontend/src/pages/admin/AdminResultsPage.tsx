import { useEffect, useState } from "react";
import { approveBatch, getBatches } from "../../api/results";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { SemesterResultBatch } from "../../types";

export default function AdminResultsPage() {
  const [batches, setBatches] = useState<SemesterResultBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [workingId, setWorkingId] = useState<number | null>(null);

  async function loadBatches() {
    setError("");
    try {
      const { data } = await getBatches();
      setBatches(data);
    } catch {
      setError("Failed to load result batches.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadBatches();
  }, []);

  async function updateBatch(batch: SemesterResultBatch, action: "approve" | "reject") {
    setWorkingId(batch.id);
    setError("");
    try {
      await approveBatch(batch.id, action);
      await loadBatches();
    } catch {
      setError("You may not have permission to update this batch, or the batch could not be changed.");
    } finally {
      setWorkingId(null);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 className="fw-bold mb-1 text-white">Result Batches</h4>
          <p className="text-white mb-0">Review results uploaded by lecturers.</p>
        </div>
        <button type="button" className="btn btn-outline-secondary btn-sm text-white" onClick={() => { void loadBatches(); }}>
          Refresh
        </button>
      </div>

      {error && <div className="alert alert-danger py-2">{error}</div>}

      {batches.length === 0 ? (
        <div className="alert alert-info">No result batches have been uploaded yet.</div>
      ) : (
        <div className="table-responsive card border-0 shadow-sm">
          <table className="table table-hover mb-0 align-middle">
            <thead className="table-light">
              <tr>
                <th>Session</th>
                <th>Semester</th>
                <th>Programme</th>
                <th>Status</th>
                <th>Created</th>
                <th className="text-end">Action</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((batch) => (
                <tr key={batch.id}>
                  <td>
                    {batch.session_name}
                    <div className="small mt-2">
                      {batch.progress.courses.map((course) => (
                        <div key={course.allocation} className={course.submitted ? "text-success" : "text-danger"}>
                          {course.submitted ? "✓" : "○"} {course.course_code} - {course.course_title}
                          · Allocation {course.allocation} · {course.lecturer} ({course.result_count} rows)
                        </div>
                      ))}
                    </div>
                  </td>
                  <td>{batch.semester}</td>
                  <td>{batch.programme_type}</td>
                  <td>
                    <span className={`badge text-bg-${batch.status === "APPROVED" ? "success" : batch.status === "REJECTED" ? "danger" : "warning"}`}>
                      {batch.status}
                    </span>
                  </td>
                  <td>
                    {batch.progress.submitted_course_count}/{batch.progress.expected_course_count} submitted
                    <div className="small text-muted">
                      {batch.progress.courses.filter((course) => !course.submitted).map((course) => course.course_code).join(", ") || "All courses"}
                    </div>
                  </td>
                  <td className="text-end">
                    {batch.status === "PENDING" && (
                      <>
                        <button
                          type="button"
                          className="btn btn-sm btn-success me-2"
                          disabled={workingId === batch.id || batch.progress.missing_course_count > 0}
                          onClick={() => { void updateBatch(batch, "approve"); }}
                        >
                          {batch.progress.missing_course_count > 0 ? "Waiting for courses" : "Approve"}
                        </button>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger"
                          disabled={workingId === batch.id}
                          onClick={() => { void updateBatch(batch, "reject"); }}
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {batch.status === "REJECTED" && <span className="text-muted small">Waiting for re-upload</span>}
                    {batch.status === "APPROVED" && <span className="text-muted small">Published</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
