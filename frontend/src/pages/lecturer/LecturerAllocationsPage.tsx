import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMyAllocations } from "../../api/courses";
import api from "../../api/client";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { CourseAllocation } from "../../types";

const SEMESTER_LABEL: Record<string, string> = {
  FIRST: "First Semester",
  SECOND: "Second Semester",
};

export default function LecturerAllocationsPage() {
  const [allocations, setAllocations] = useState<CourseAllocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMyAllocations()
      .then(({ data }) => setAllocations(data))
      .catch(() => setError("Failed to load your course allocations."))
      .finally(() => setLoading(false));
  }, []);

  const handleDownloadStudents = async (allocationId: number) => {
    try {
      const { data } = await api.get(`/courses/allocations/${allocationId}/students/export/`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([data], { type: "text/csv;charset=utf-8;" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `students-${allocationId}.csv`;
      anchor.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Could not download the student list for this course.");
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4" style={{ maxWidth: 900 }}>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="fw-bold mb-0 text-white">My Courses</h4>
        <span className="badge bg-primary fs-6">{allocations.length}</span>
      </div>

      {error && <div className="alert alert-danger py-2">{error}</div>}

      {allocations.length === 0 && !error ? (
        <div className="alert alert-info">
          You have no course allocations in the current academic session.
          Course allocations are assigned by the admin — contact the PG Coordinator
          if you are expecting a course.
        </div>
      ) : (
        <div className="row g-3">
          {allocations.map((a) => (
            <div key={a.id} className="col-md-6">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body d-flex flex-column">
                  <div className="d-flex justify-content-between align-items-start mb-1">
                    <h5 className="fw-bold mb-0"><code>{a.course_code}</code></h5>
                    <span className="badge bg-light text-dark border">
                      {a.credit_units} CU
                    </span>
                  </div>
                  <div className="fw-semibold mb-1">{a.course_title}</div>
                  <div className="text-muted small mb-3">
                    {a.session_name} · {SEMESTER_LABEL[a.semester] ?? a.semester} ·{" "}
                    {a.enrolled_count} enrolled student{a.enrolled_count === 1 ? "" : "s"}
                  </div>
                  <div className="mt-auto d-flex gap-2 flex-wrap">
                    <Link
                      to={`/lecturer/materials/${a.id}`}
                      className="btn btn-sm btn-outline-secondary flex-fill"
                    >
                      📁 Materials
                    </Link>
                    <Link
                      to={`/lecturer/results/upload?allocation=${a.id}`}
                      className="btn btn-sm btn-primary btn-download flex-fill"
                    >
                      📊 Upload Results
                    </Link>
                    <button
                      type="button"
                      className="btn btn-sm btn-success flex-fill"
                      onClick={() => void handleDownloadStudents(a.id)}
                    >
                      ⬇ Download Students
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
