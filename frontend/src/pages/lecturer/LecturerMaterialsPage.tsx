import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { getMyAllocations, getMaterials, uploadMaterial } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { CourseAllocation, CourseMaterial } from "../../types";

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
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
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
      const { data } = await uploadMaterial(pk, fd);
      setMaterials((prev) => [data, ...prev]);
      setTitle("");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      setUploadSuccess("Material uploaded successfully.");
    } catch {
      setUploadError("Upload failed. Check file type and size (max 20 MB).");
    } finally {
      setUploading(false);
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
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/lecturer/dashboard">Dashboard</Link></li>
          <li className="breadcrumb-item active">Course Materials</li>
        </ol>
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
                  <div className="text-muted small ms-4">
                    Uploaded {new Date(m.uploaded_at).toLocaleDateString("en-GB", {
                      day: "numeric", month: "short", year: "numeric",
                    })}
                  </div>
                </div>
                <a
                  href={m.file}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-sm btn-outline-primary"
                >
                  Download
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
