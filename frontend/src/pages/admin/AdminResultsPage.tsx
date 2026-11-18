import { Fragment, useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { approveBatch, getBatches } from "../../api/results";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { SemesterResultBatch } from "../../types";

function getApiErrorMessage(error: unknown, fallback: string) {
  if (isAxiosError(error)) {
    const data = error.response?.data;
    const detail = data?.detail;
    const outstanding = data?.outstanding_courses;
    if (Array.isArray(outstanding)) {
      const summaries = outstanding.map((item) => {
        if (!item || typeof item !== "object") return "";
        const course = item as {
          course_code?: unknown;
          submitted?: unknown;
          expected?: unknown;
          missing_students?: unknown;
        };
        const missing = Array.isArray(course.missing_students)
          ? course.missing_students.map((student) => {
            if (!student || typeof student !== "object") return "";
            const registration = (student as { matric_number?: unknown }).matric_number;
            return typeof registration === "string" ? registration : "";
          }).filter(Boolean).join(", ")
          : "";
        return `${String(course.course_code ?? "Course")}: ${String(course.submitted ?? 0)}/${String(course.expected ?? 0)} results${missing ? `; missing ${missing}` : ""}`;
      }).filter(Boolean);
      if (summaries.length) {
        return `${typeof detail === "string" ? `${detail} ` : ""}${summaries.join("; ")}`;
      }
    }
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export default function AdminResultsPage() {
  const [batches, setBatches] = useState<SemesterResultBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [workingId, setWorkingId] = useState<number | null>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);

  async function loadBatches() {
    setError("");
    try {
      const { data } = await getBatches();
      setBatches(data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to load result batches."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void getBatches()
      .then(({ data }) => setBatches(data))
      .catch((err: unknown) => {
        setError(getApiErrorMessage(err, "Failed to load result batches."));
      })
      .finally(() => setLoading(false));
  }, []);

  async function updateBatch(batch: SemesterResultBatch, action: "approve" | "reject") {
    setWorkingId(batch.id);
    setError("");
    try {
      await approveBatch(batch.id, action);
      await loadBatches();
    } catch (err) {
      setError(getApiErrorMessage(
        err,
        "You may not have permission to update this batch, or the batch could not be changed."
      ));
    } finally {
      setWorkingId(null);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 className="fw-bold mb-1">Result Batches</h4>
          <p className="text-muted mb-0">Review results uploaded by lecturers.</p>
        </div>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => { void loadBatches(); }}>
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
                <th>Course progress</th>
                <th className="text-end">Action</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((batch) => (
                <Fragment key={batch.id}>
                <tr>
                  <td>
                    {batch.session_name}
                  </td>
                  <td>{batch.semester}</td>
                  <td>{batch.programme_type}</td>
                  <td>
                    <span className={`badge text-bg-${batch.status === "APPROVED" ? "success" : batch.status === "REJECTED" ? "danger" : "warning"}`}>
                      {batch.status}
                    </span>
                  </td>
                  <td>
                    {batch.progress.submitted_course_count}/{batch.progress.expected_course_count} complete
                    <div className="small text-muted">
                      {batch.progress.missing_course_count > 0
                        ? `${batch.progress.missing_course_count} course(s) outstanding`
                        : `${batch.progress.no_enrollment_course_count} course(s) have no approved enrollments`}
                    </div>
                    <button
                      type="button"
                      className="btn btn-sm btn-link px-0"
                      aria-expanded={selectedBatchId === batch.id}
                      onClick={() => setSelectedBatchId(
                        selectedBatchId === batch.id ? null : batch.id
                      )}
                    >
                      {selectedBatchId === batch.id ? "Hide course details" : "Review course progress"}
                    </button>
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
                          {batch.progress.missing_course_count > 0 ? "Incomplete results" : "Approve"}
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
                {selectedBatchId === batch.id && (
                  <tr>
                    <td colSpan={6} className="bg-light p-3">
                      {batch.progress.courses.length === 0 ? (
                        <div className="alert alert-warning mb-0">
                          No course allocations match this batch&apos;s session, semester, and programme.
                        </div>
                      ) : (
                        <div className="table-responsive">
                          <table className="table table-sm table-bordered bg-white mb-0 align-middle">
                            <thead className="table-light">
                              <tr>
                                <th>Course</th>
                                <th>Lecturer</th>
                                <th>Submitted / expected</th>
                                <th>Status</th>
                                <th>{batch.status === "APPROVED" ? "Submitted results" : "Outstanding / submitted results"}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {batch.progress.courses.map((course) => {
                                const badge = {
                                  COMPLETE: ["success", "Complete"],
                                  INCOMPLETE: ["warning", "Incomplete"],
                                  NOT_UPLOADED: ["danger", "Not uploaded"],
                                  NO_ENROLLMENTS: ["secondary", "No approved enrollments"],
                                }[course.status];
                                return (
                                  <tr key={course.allocation}>
                                    <td>
                                      <strong>{course.course_code}</strong> — {course.course_title}
                                      <div className="small text-muted">
                                        {course.programme_name} · Allocation {course.allocation}
                                      </div>
                                    </td>
                                    <td>
                                      {course.lecturer || "Not assigned"}
                                      {course.lecturer_email && (
                                        <div className="small text-muted">{course.lecturer_email}</div>
                                      )}
                                    </td>
                                    <td>{course.result_count} / {course.expected_result_count}</td>
                                    <td><span className={`badge text-bg-${badge[0]}`}>{badge[1]}</span></td>
                                    <td>
                                      {course.submitted_results.length > 0 && (
                                        <ul className="mb-2 ps-3">
                                          {course.submitted_results.map((result) => (
                                            <li key={result.matric_number}>
                                              {result.matric_number} — {result.student_name}:{" "}
                                              {result.score} ({result.grade}, {result.grade_point} GP)
                                            </li>
                                          ))}
                                        </ul>
                                      )}
                                      {course.missing_students.length > 0 && (
                                        <div>
                                          <strong>Missing:</strong>
                                          <ul className="mb-0 ps-3">
                                            {course.missing_students.map((student) => (
                                              <li key={student.matric_number}>
                                                {student.matric_number} — {student.student_name}
                                              </li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                      {course.submitted_results.length === 0 && course.missing_students.length === 0 && "—"}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
