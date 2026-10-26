import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { isAxiosError } from "axios";
import { dropEnrollment, getMyEnrollments, getMaterials } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { Enrollment, CourseMaterial } from "../../types";

function fileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📄";
  if (["ppt", "pptx"].includes(ext ?? "")) return "📊";
  if (["doc", "docx"].includes(ext ?? "")) return "📝";
  if (["xls", "xlsx"].includes(ext ?? "")) return "📈";
  if (["zip", "rar"].includes(ext ?? "")) return "🗜️";
  return "📎";
}

function StatusBadge({ status }: { status: Enrollment["status"] }) {
  const map = {
    APPROVED: "success",
    PENDING: "warning",
    REJECTED: "danger",
  } as const;
  return <span className={`badge bg-${map[status]}`}>{status}</span>;
}

function CourseMaterialsRow({ allocationId }: { allocationId: number }) {
  const [materials, setMaterials] = useState<CourseMaterial[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMaterials(allocationId)
      .then(({ data }) => setMaterials(data))
      .catch((err: unknown) => {
        const detail = isAxiosError<{ detail?: string }>(err)
          ? err.response?.data?.detail
          : undefined;
        setError(detail ?? "Failed to load materials.");
      })
      .finally(() => setLoading(false));
  }, [allocationId]);

  if (loading) return (
    <div className="p-3 text-muted small">
      <span className="spinner-border spinner-border-sm me-2" />Loading materials…
    </div>
  );
  if (error) return <div className="p-3 text-danger small">{error}</div>;
  if (materials.length === 0) return (
    <div className="p-3 text-muted small">No materials uploaded by the lecturer yet.</div>
  );

  return (
    <ul className="list-group list-group-flush">
      {materials.map((m) => (
        <li
          key={m.id}
          className="list-group-item d-flex justify-content-between align-items-center py-2 ps-4"
        >
          <div>
            <span className="me-2">{fileIcon(m.file)}</span>
            <span>{m.title}</span>
            {m.description && (
              <div className="text-muted small ms-4" style={{ whiteSpace: "pre-wrap" }}>
                {m.description}
              </div>
            )}
            <span className="text-muted small ms-2">
              {new Date(m.uploaded_at).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })}
            </span>
          </div>
          {m.file_available ? (
            <a
              href={m.file}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-sm btn-outline-primary"
            >
              Download
            </a>
          ) : (
            <span className="text-danger small" title="The file is missing from server storage.">
              File unavailable
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

export default function StudentCoursesPage() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [droppingId, setDroppingId] = useState<number | null>(null);
  const [enrollmentActionMessage, setEnrollmentActionMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    getMyEnrollments()
      .then(({ data }) => setEnrollments(data))
      .catch(() => setError("Failed to load your courses. Please try again."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const approved = enrollments.filter((e) => e.status === "APPROVED");
  const others = enrollments.filter((e) => e.status !== "APPROVED");

  function toggleMaterials(allocationId: number) {
    setExpandedId((prev) => (prev === allocationId ? null : allocationId));
  }

  async function handleDrop(enrollment: Enrollment) {
    if (!window.confirm(`Drop ${enrollment.course_code} — ${enrollment.course_title}?`)) return;
    setDroppingId(enrollment.id);
    setEnrollmentActionMessage("");
    try {
      await dropEnrollment(enrollment.id);
      setEnrollments((prev) => prev.filter((item) => item.id !== enrollment.id));
      setEnrollmentActionMessage({
        type: "success",
        text: `${enrollment.course_code} enrollment dropped.`,
      });
      if (expandedId === enrollment.allocation) setExpandedId(null);
    } catch (err: unknown) {
      const detail = isAxiosError<{ detail?: string }>(err)
        ? err.response?.data?.detail
        : undefined;
      setEnrollmentActionMessage({
        type: "error",
        text: detail ?? "Could not drop this enrollment. Please try again.",
      });
    } finally {
      setDroppingId(null);
    }
  }

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="fw-bold mb-0 text-white">My Courses</h4>
          <p className="text-white small mb-0">
            {approved.length} approved &middot; {others.length} pending / rejected
          </p>
        </div>
        <Link to="/student/dashboard" className="btn btn-outline-secondary btn-sm text-white">← Dashboard</Link>
      </div>

      {error ? (
        <div className="alert alert-danger">{error}</div>
      ) : enrollments.length === 0 ? (
        <div className="alert alert-info">
          You are not enrolled in any courses yet. Contact the admin to get enrolled.
        </div>
      ) : (
        <>
          {enrollmentActionMessage && (
            <div className={`alert alert-${enrollmentActionMessage.type === "success" ? "success" : "danger"}`}>
              {enrollmentActionMessage.text}
            </div>
          )}
          {approved.length > 0 && (
            <div className="card border-0 shadow-sm mb-4">
              <div className="card-header bg-white fw-semibold">
                Enrolled Courses
                <span className="badge bg-success ms-2">{approved.length}</span>
              </div>
              <div className="list-group list-group-flush">
                {approved.map((e) => (
                  <div key={e.id}>
                    <div className="list-group-item">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <span className="fw-semibold me-2">
                            <code>{e.course_code}</code>
                          </span>
                          {e.course_title}
                          <div className="text-muted small mt-1">
                            {e.credit_units} CU &middot; Lecturer: {e.lecturer_name}
                          </div>
                        </div>
                        <div className="d-flex align-items-center gap-2">
                          <StatusBadge status={e.status} />
                          <button
                            type="button"
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => toggleMaterials(e.allocation)}
                          >
                            {expandedId === e.allocation ? "Hide Materials ▲" : "Materials ▼"}
                          </button>
                          <button
                            type="button"
                            className="btn btn-sm btn-outline-danger"
                            disabled={droppingId === e.id}
                            onClick={() => { void handleDrop(e); }}
                          >
                            {droppingId === e.id ? "Dropping…" : "Drop"}
                          </button>
                        </div>
                      </div>
                    </div>
                    {expandedId === e.allocation && (
                      <div className="bg-light border-bottom">
                        <CourseMaterialsRow allocationId={e.allocation} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {others.length > 0 && (
            <div className="card border-0 shadow-sm">
              <div className="card-header bg-white fw-semibold text-muted">
                Pending / Rejected Enrollments
              </div>
              <div className="table-responsive">
                <table className="table table-sm mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Code</th>
                      <th>Title</th>
                      <th>Credit Units</th>
                      <th>Lecturer</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {others.map((e) => (
                      <tr key={e.id}>
                        <td><code>{e.course_code}</code></td>
                        <td>{e.course_title}</td>
                        <td>{e.credit_units}</td>
                        <td>{e.lecturer_name}</td>
                        <td><StatusBadge status={e.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
