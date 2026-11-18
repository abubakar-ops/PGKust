import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMyEnrollments } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { Enrollment } from "../../types";

export default function StudentMaterialsPage() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMyEnrollments()
      .then(({ data }) => setEnrollments(data))
      .catch(() => setError("Failed to load your courses."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const approved = enrollments.filter((e) => e.status === "APPROVED");

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="fw-bold mb-1">Course Materials</h4>
          <p className="text-muted small mb-0">
            Lecture notes, slides and other materials uploaded by your lecturers
          </p>
        </div>
        <Link to="/student/dashboard" className="btn btn-outline-secondary btn-sm">← Dashboard</Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {approved.length === 0 ? (
        <div className="alert alert-info">
          You have no approved course enrollments yet. Once the admin approves your
          enrollment, your course materials will appear here.
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white fw-semibold">
            Your Courses
            <span className="badge bg-success ms-2">{approved.length}</span>
          </div>
          <div className="list-group list-group-flush">
            {approved.map((e) => (
              <div key={e.id} className="list-group-item">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <span className="fw-semibold me-2"><code>{e.course_code}</code></span>
                    {e.course_title}
                    <div className="text-muted small mt-1">
                      {e.credit_units} CU &middot; Lecturer: {e.lecturer_name}
                    </div>
                  </div>
                  <Link
                    to={`/student/materials/${e.allocation}`}
                    className="btn btn-sm btn-primary text-nowrap"
                  >
                    📚 View Materials
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
