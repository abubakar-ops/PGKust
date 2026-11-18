import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { getMyAllocations, getTimetable } from "../../api/courses";
import { getSupervisedStudents } from "../../api/auth";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { CourseAllocation, TimetableEntry, LecturerProfile, StudentProfile } from "../../types";

export default function LecturerDashboard() {
  const { user } = useAuth();
  const [allocations, setAllocations] = useState<CourseAllocation[]>([]);
  const [timetable, setTimetable] = useState<TimetableEntry[]>([]);
  const [supervisedStudents, setSupervisedStudents] = useState<StudentProfile[]>([]);
  const [supervisedStudentsError, setSupervisedStudentsError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([
      getMyAllocations().then(({ data }) => setAllocations(data)).catch(() => { /* none */ }),
      getTimetable().then(({ data }) => setTimetable(data)).catch(() => { /* none */ }),
      getSupervisedStudents()
        .then(({ data }) => setSupervisedStudents(data))
        .catch(() => setSupervisedStudentsError("Could not load your assigned students.")),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const profile = user?.profile as LecturerProfile | null;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1 text-white">Welcome, {user?.first_name}</h4>
      <p className="text-white">{profile?.staff_id} · Lecturer</p>

      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <h6 className="text-muted">Courses This Session</h6>
              <span className="fs-3 fw-bold text-primary">{allocations.length}</span>
              <div className="mt-2">
                <Link to="/lecturer/allocations" className="btn btn-sm btn-outline-primary">View Courses →</Link>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <h6 className="text-muted">Timetable Slots</h6>
              <span className="fs-3 fw-bold text-primary">{timetable.length}</span>
              <div className="mt-2">
                <Link to="/lecturer/timetable" className="btn btn-sm btn-outline-primary">Timetable →</Link>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <h6 className="text-muted">Upload Results</h6>
              <p className="text-muted small mb-2">Submit scores for your courses</p>
              <Link to="/lecturer/results/upload" className="btn btn-sm btn-primary">Upload →</Link>
            </div>
          </div>
        </div>
      </div>

      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-bold">My Courses</div>
        <div className="table-responsive">
          <table className="table table-hover mb-0">
            <thead className="table-light">
              <tr><th>Code</th><th>Title</th><th>Semester</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {allocations.map((a) => (
                <tr key={a.id}>
                  <td><code>{a.course_code}</code></td>
                  <td>{a.course_title}</td>
                  <td>{a.semester}</td>
                  <td>
                    <Link to={`/lecturer/materials/${a.id}`} className="btn btn-sm btn-outline-secondary me-1">Materials</Link>
                    <Link to={`/lecturer/results/upload?allocation=${a.id}`} className="btn btn-sm btn-outline-primary">Results</Link>
                  </td>
                </tr>
              ))}
              {allocations.length === 0 && (
                <tr><td colSpan={4} className="text-center text-muted">No course allocations found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card border-0 shadow-sm mt-4">
        <div className="card-header bg-white fw-bold">My Supervised Students</div>
        {supervisedStudentsError ? (
          <div className="card-body text-danger">{supervisedStudentsError}</div>
        ) : (
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr><th>Name</th><th>Matric No.</th><th>Programme</th><th>Email</th><th>Phone</th></tr>
              </thead>
              <tbody>
                {supervisedStudents.map((student) => (
                  <tr key={student.id}>
                    <td>{student.full_name}</td>
                    <td>{student.matric_number}</td>
                    <td>{student.programme}</td>
                    <td>{student.email}</td>
                    <td>{student.phone_number || "—"}</td>
                  </tr>
                ))}
                {supervisedStudents.length === 0 && (
                  <tr><td colSpan={5} className="text-center text-muted">No students are currently assigned to you.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
