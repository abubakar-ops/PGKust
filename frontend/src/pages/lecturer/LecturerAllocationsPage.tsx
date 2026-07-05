import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMyAllocations } from "../../api/courses";
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

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4" style={{ maxWidth: 900 }}>
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/lecturer/dashboard">Dashboard</Link></li>
          <li className="breadcrumb-item active">My Courses</li>
        </ol>
      </nav>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="fw-bold mb-0">My Courses This Session</h4>
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
                  <div className="mt-auto d-flex gap-2">
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
