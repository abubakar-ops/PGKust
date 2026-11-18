import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { isAxiosError } from "axios";
import { deleteMaterial, getMyAllocations, getMaterials, uploadMaterial } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { CourseAllocation, CourseMaterial } from "../../types";

function requestFailureMessage(error: unknown, fallback: string) {
  if (isAxiosError<{ detail?: unknown; errors?: unknown }>(error)) {
    const response = error.response?.data;
    const detail = response?.detail ?? response?.errors;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object") {
      const messages = Object.values(detail).flatMap((value) =>
        Array.isArray(value) ? value : [value],
      );
      const message = messages.find((value): value is string => typeof value === "string");
      if (message) return message;
    }
    if (error.response) {
      return `Request failed with HTTP ${error.response.status}. Check the server logs for details.`;
    }
    if (error.request) {
      return "No response received from the server. Check that the backend is running and try again.";
    }
  }
  return fallback;
}

function fileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "📄";
  if (["ppt", "pptx"].includes(ext ?? "")) return "📊";
  if (["doc", "docx"].includes(ext ?? "")) return "📝";
  if (["xls", "xlsx"].includes(ext ?? "")) return "📈";
  if (["zip", "rar"].includes(ext ?? "")) return "🗜️";
  return "📎";
}

export default function LecturerMaterialsPage() {
  const { allocationId } = useParams<{ allocationId: string }>();
  const pk = Number(allocationId);

  const [allocation, setAllocation] = useState<CourseAllocation | null>(null);
  const [materials, setMaterials] = useState<CourseMaterial[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void Promise.all([
      getMyAllocations().then(({ data }) => {
        const found = data.find((a) => a.id === pk) ?? null;
        setAllocation(found);
        if (!found) setPageError("Course allocation not found.");
      }),
      getMaterials(pk).then(({ data }) => setMaterials(data)),
    ])
      .catch(() => setPageError("Failed to load course data."))
      .finally(() => setLoading(false));
  }, [pk]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) { setUploadError("Please select a file."); return; }
    setUploading(true);
    setUploadError("");
    setUploadSuccess("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", title.trim() || file.name);
      fd.append("description", description.trim());
      const { data } = await uploadMaterial(pk, fd);
      setMaterials((prev) => [data, ...prev]);
      setTitle("");
      setDescription("");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      setUploadSuccess("Material uploaded successfully.");
    } catch (error: unknown) {
      setUploadError(requestFailureMessage(error, "Upload could not be completed. Please try again."));
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(material: CourseMaterial) {
    if (!window.confirm(`Delete "${material.title}"? This also removes its file.`)) return;
    setDeletingId(material.id);
    setDeleteError("");
    try {
      await deleteMaterial(pk, material.id);
      setMaterials((prev) => prev.filter((item) => item.id !== material.id));
    } catch (error: unknown) {
      setDeleteError(requestFailureMessage(error, "Could not delete this material. Please try again."));
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) return <LoadingSpinner />;
  if (pageError) return (
    <div className="container py-4">
      <div className="alert alert-danger">{pageError}</div>
      <Link to="/lecturer/dashboard" className="btn btn-outline-secondary">← Back to Dashboard</Link>
    </div>
  );

  return (
    <div className="container py-4" style={{ maxWidth: 800 }}>
      <nav aria-label="breadcrumb" className="mb-3">
       <h4 className="fw-bold mb-0 text-white">Course Materials</h4>
      </nav>

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body">
          <h5 className="fw-bold mb-1">
            <code className="me-2">{allocation?.course_code}</code>
            {allocation?.course_title}
          </h5>
          <span className="text-muted small">
            {allocation?.session_name} &middot; {allocation?.semester} Semester
          </span>
        </div>
      </div>

      {/* Upload Form */}
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">Upload New Material</div>
        <div className="card-body">
          <form onSubmit={(e) => { void handleUpload(e); }}>
            <div className="mb-3">
              <label className="form-label">
                Title <span className="text-muted small">(optional — defaults to filename)</span>
              </label>
              <input
                type="text"
                className="form-control"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Week 3 Lecture Slides"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Description <span className="text-muted small">(optional)</span></label>
              <textarea
                className="form-control"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add details about this material"
              />
            </div>
            <div className="mb-3">
              <label className="form-label">File <span className="text-danger">*</span></label>
              <input
                ref={fileRef}
                type="file"
                className="form-control"
                accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <div className="form-text">Allowed: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, ZIP, RAR &middot; Max 20 MB</div>
            </div>
            {uploadError && <div className="alert alert-danger py-2 mb-3">{uploadError}</div>}
            {uploadSuccess && <div className="alert alert-success py-2 mb-3">{uploadSuccess}</div>}
            <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
              {uploading ? (
                <><span className="spinner-border spinner-border-sm me-2" />Uploading…</>
              ) : "Upload Material"}
            </button>
          </form>
        </div>
      </div>

      {/* Materials List */}
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-semibold d-flex justify-content-between align-items-center">
          <span>Uploaded Materials</span>
          <span className="badge bg-secondary">{materials.length}</span>
        </div>
        {deleteError && <div className="alert alert-danger m-3 mb-0">{deleteError}</div>}
        {materials.length === 0 ? (
          <div className="card-body text-center text-muted py-4">
            No materials uploaded yet for this course.
          </div>
        ) : (
          <ul className="list-group list-group-flush">
            {materials.map((m) => (
              <li
                key={m.id}
                className="list-group-item d-flex justify-content-between align-items-center py-3"
              >
                <div>
                  <span className="me-2 fs-5">{fileIcon(m.file)}</span>
                  <span className="fw-semibold">{m.title}</span>
                  {m.description && (
                    <div className="text-muted small ms-4" style={{ whiteSpace: "pre-wrap" }}>
                      {m.description}
                    </div>
                  )}
                  <div className="text-muted small ms-4">
                    Uploaded {new Date(m.uploaded_at).toLocaleDateString("en-GB", {
                      day: "numeric", month: "short", year: "numeric",
                    })}
                  </div>
                </div>
                <div className="d-flex align-items-center gap-2">
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
                      File missing — re-upload
                    </span>
                  )}
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-danger"
                    disabled={deletingId === m.id}
                    onClick={() => { void handleDelete(m); }}
                  >
                    {deletingId === m.id ? "Deleting…" : "Delete"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
