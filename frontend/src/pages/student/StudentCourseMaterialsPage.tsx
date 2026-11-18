import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { isAxiosError } from "axios";
import { getMyEnrollments, getMaterials } from "../../api/courses";
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

export default function StudentCourseMaterialsPage() {
  const { allocationId } = useParams<{ allocationId: string }>();
  const pk = Number(allocationId);

  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [materials, setMaterials] = useState<CourseMaterial[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void Promise.all([
      getMyEnrollments().then(({ data }) => {
        setEnrollment(data.find((e) => e.allocation === pk) ?? null);
      }),
      getMaterials(pk).then(({ data }) => setMaterials(data)),
    ])
      .catch((err: unknown) => {
        const detail = isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail : undefined;
        setError(detail ?? "Failed to load course materials.");
      })
      .finally(() => setLoading(false));
  }, [pk]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4" style={{ maxWidth: 800 }}>
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/student/materials">Course Materials</Link></li>
          <li className="breadcrumb-item active">{enrollment?.course_code ?? "Course"}</li>
        </ol>
      </nav>

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body">
          <h5 className="fw-bold mb-1">
            <code className="me-2">{enrollment?.course_code}</code>
            {enrollment?.course_title}
          </h5>
          {enrollment && (
            <span className="text-muted small">Lecturer: {enrollment.lecturer_name}</span>
          )}
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-semibold d-flex justify-content-between align-items-center">
          <span>Uploaded Materials</span>
          <span className="badge bg-secondary">{materials.length}</span>
        </div>
        {!error && materials.length === 0 ? (
          <div className="card-body text-center text-muted py-4">
            No materials uploaded by the lecturer yet.
          </div>
        ) : (
          <ul className="list-group list-group-flush">
            {materials.map((m) => (
              <li key={m.id} className="list-group-item py-3">
                <div className="d-flex justify-content-between align-items-start">
                  <div>
                    <span className="me-2 fs-5">{fileIcon(m.file)}</span>
                    <span className="fw-semibold">{m.title}</span>
                    <div className="text-muted small ms-4">
                      <code>{m.course_code}</code> {m.course_title}
                    </div>
                    {m.description && (
                      <div className="text-muted small ms-4 mt-1">{m.description}</div>
                    )}
                    <div className="text-muted small ms-4 mt-1">
                      Uploaded {new Date(m.uploaded_at).toLocaleDateString("en-GB", {
                        day: "numeric", month: "short", year: "numeric",
                      })}
                    </div>
                  </div>
                  {m.file_available ? (
                    <a
                      href={m.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-primary text-nowrap"
                    >
                      View / Download
                    </a>
                  ) : (
                    <span className="text-danger small">File missing from media storage</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
