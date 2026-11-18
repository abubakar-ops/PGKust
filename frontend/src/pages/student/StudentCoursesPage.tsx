import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMyEnrollments } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { Enrollment } from "../../types";

function StatusBadge({ status }: { status: Enrollment["status"] }) {
  const map = {
    APPROVED: "success",
    PENDING: "warning",
    REJECTED: "danger",
  } as const;
  return <span className={`badge bg-${map[status]}`}>{status}</span>;
}

export default function StudentCoursesPage() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyEnrollments()
      .then(({ data }) => setEnrollments(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const approved = enrollments.filter((e) => e.status === "APPROVED");
  const others = enrollments.filter((e) => e.status !== "APPROVED");

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="fw-bold mb-0">My Courses</h4>
          <p className="text-muted small mb-0">
            {approved.length} approved &middot; {others.length} pending / rejected
          </p>
        </div>
        <Link to="/student/dashboard" className="btn btn-outline-secondary btn-sm">← Dashboard</Link>
      </div>

      {enrollments.length === 0 ? (
        <div className="alert alert-info">
          You are not enrolled in any courses yet. Contact the admin to get enrolled.
        </div>
      ) : (
        <>
          {approved.length > 0 && (
            <div className="card border-0 shadow-sm mb-4">
              <div className="card-header bg-white fw-semibold">
                Enrolled Courses
                <span className="badge bg-success ms-2">{approved.length}</span>
              </div>
              <div className="list-group list-group-flush">
                {approved.map((e) => (
                  <div key={e.id} className="list-group-item">
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
                        <Link
                          to={`/student/materials/${e.allocation}`}
                          className="btn btn-sm btn-primary text-nowrap"
                        >
                          📚 Materials
                        </Link>
                      </div>
                    </div>
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
