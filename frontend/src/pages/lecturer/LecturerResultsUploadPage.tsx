import { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { isAxiosError } from "axios";
import { getMyAllocations } from "../../api/courses";
import { downloadScoreSheetTemplate, uploadResultsExcel } from "../../api/results";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { CourseAllocation, ExcelUploadResponse } from "../../types";

export default function LecturerResultsUploadPage() {
  const [searchParams] = useSearchParams();
  const preselected = Number(searchParams.get("allocation")) || null;

  const [allocations, setAllocations] = useState<CourseAllocation[]>([]);
  const [allocationId, setAllocationId] = useState<number | null>(preselected);
  const [loading, setLoading] = useState(true);

  const [downloading, setDownloading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<ExcelUploadResponse | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getMyAllocations()
      .then(({ data }) => {
        setAllocations(data);
        setAllocationId((prev) => {
          const valid = (id: number | null) => id !== null && data.some((a) => a.id === id);
          if (valid(prev)) return prev;
          if (valid(preselected)) return preselected;
          return data[0]?.id ?? null;
        });
      })
      .catch(() => setError("Failed to load your course allocations."))
      .finally(() => setLoading(false));
  }, [preselected]);

  const allocation = allocations.find((a) => a.id === allocationId) ?? null;

  function apiErrorDetail(err: unknown): string | undefined {
    return isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail : undefined;
  }

  async function handleDownloadTemplate() {
    if (!allocationId || !allocation) {
      setError(allocations.length === 0
        ? "You have no course allocations in the current session. Ask the admin to allocate a course to you."
        : "Select a course first.");
      return;
    }
    setDownloading(true);
    setError("");
    try {
      const { data } = await downloadScoreSheetTemplate(allocationId);
      const url = URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${allocation.course_code}_${allocation.session_name.replace("/", "_")}_SCORE_SHEET.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      let detail = apiErrorDetail(err);
      // blob-typed requests deliver error JSON as a Blob — decode it
      if (!detail && isAxiosError(err) && err.response?.data instanceof Blob) {
        try {
          detail = (JSON.parse(await err.response.data.text()) as { detail?: string }).detail;
        } catch { /* not JSON — keep generic message */ }
      }
      setError(detail ?? "Failed to download the score sheet template.");
    } finally {
      setDownloading(false);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!allocationId) { setError("Select a course first."); return; }
    if (!file) { setError("Select the filled score sheet (.xlsx)."); return; }
    setUploading(true);
    setError("");
    setReport(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await uploadResultsExcel(allocationId, fd);
      setReport(data);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setError(apiErrorDetail(err) ?? "Upload failed. Make sure you used the downloaded template.");
    } finally {
      setUploading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4" style={{ maxWidth: 820 }}>
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/lecturer/dashboard">Dashboard</Link></li>
          <li className="breadcrumb-item active">Upload Results</li>
        </ol>
      </nav>

      {error && <div className="alert alert-danger py-2">{error}</div>}

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">1. Select Course</div>
        <div className="card-body">
          <select
            className="form-select"
            value={allocationId ?? ""}
            onChange={(e) => { setAllocationId(Number(e.target.value) || null); setReport(null); setError(""); }}
          >
            <option value="">— Select a course allocation —</option>
            {allocations.map((a) => (
              <option key={a.id} value={a.id}>
                {a.course_code} — {a.course_title} ({a.session_name}, {a.semester})
              </option>
            ))}
          </select>
          {allocations.length === 0 && (
            <div className="form-text text-danger">
              You have no course allocations in the current session.
            </div>
          )}
        </div>
      </div>

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">2. Download Blank Score Sheet</div>
        <div className="card-body">
          <p className="text-muted small mb-2">
            The template already contains the registration number and name of every student
            enrolled in this course. Simply fill in the <strong>CA</strong> and{" "}
            <strong>Exam</strong> columns. Each student&apos;s total score (CA + Exam) must not
            exceed 100.
          </p>
          <button
            type="button"
            className="btn btn-primary btn-download"
            disabled={downloading}
            onClick={() => { void handleDownloadTemplate(); }}
          >
            {downloading ? (
              <><span className="spinner-border spinner-border-sm me-2" />Preparing…</>
            ) : "⬇ Download Score Sheet Template (.xlsx)"}
          </button>
        </div>
      </div>

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">3. Upload Filled Score Sheet</div>
        <div className="card-body">
          <form onSubmit={(e) => { void handleUpload(e); }}>
            <div className="mb-3">
              <input
                ref={fileRef}
                type="file"
                className="form-control"
                accept=".xlsx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <div className="form-text">Excel (.xlsx) only — use the downloaded template.</div>
            </div>
            <button type="submit" className="btn btn-primary btn-download" disabled={uploading || !file || !allocationId}>
              {uploading ? (
                <><span className="spinner-border spinner-border-sm me-2" />Uploading…</>
              ) : "Upload Results"}
            </button>
          </form>
        </div>
      </div>

      {report && (
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white fw-semibold">Upload Report</div>
          <div className="card-body">
            <div className="alert alert-success py-2">
              {report.uploaded} result{report.uploaded === 1 ? "" : "s"} uploaded.
              Batch status: <strong>{report.batch_status}</strong> (results become visible to
              students after PG Coordinator approval).
            </div>
            {report.errors.length > 0 && (
              <>
                <h6 className="text-danger">Rows with problems ({report.errors.length})</h6>
                <div className="table-responsive mb-3">
                  <table className="table table-sm">
                    <thead className="table-light">
                      <tr><th>Excel Row</th><th>Registration No.</th><th>Problem</th></tr>
                    </thead>
                    <tbody>
                      {report.errors.map((e, i) => (
                        <tr key={i}>
                          <td>{e.row}</td>
                          <td><code>{e.registration_no}</code></td>
                          <td>{e.detail}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {report.students_without_scores.length > 0 && (
              <div className="alert alert-warning py-2 mb-0">
                <strong>No score uploaded for:</strong>{" "}
                {report.students_without_scores.join(", ")}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
