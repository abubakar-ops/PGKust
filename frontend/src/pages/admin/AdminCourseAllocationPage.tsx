import { useState, useEffect, useCallback } from "react";
import {
  getCourses, adminAllocateCourse, adminGetAllocations, getCurrentSession,
} from "../../api/courses";
import { getAllLecturers } from "../../api/auth";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { Course, CourseAllocation, LecturerProfile, AcademicSession, Semester } from "../../types";

export default function AdminCourseAllocationPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [lecturers, setLecturers] = useState<LecturerProfile[]>([]);
  const [session, setSession] = useState<AcademicSession | null>(null);
  const [allocations, setAllocations] = useState<CourseAllocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [courseId, setCourseId] = useState<number | "">("");
  const [lecturerId, setLecturerId] = useState<number | "">("");
  const [semester, setSemester] = useState<Semester>("FIRST");

  const loadAllocations = useCallback(async () => {
    const { data } = await adminGetAllocations();
    setAllocations(data);
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    Promise.all([
      getCourses().then(({ data }) => setCourses(data)),
      getAllLecturers("ACTIVE").then(({ data }) => setLecturers(data)),
      getCurrentSession().then(({ data }) => setSession(data)).catch(() => setSession(null)),
      loadAllocations(),
    ])
      .catch(() => setError("Failed to load course allocation data."))
      .finally(() => setLoading(false));
  }, [loadAllocations]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!courseId || !lecturerId || !session) {
      setError("Select a course, a lecturer, and ensure a current session exists.");
      return;
    }
    setSubmitting(true);
    try {
      await adminAllocateCourse({
        course: courseId,
        lecturer: lecturerId,
        session: session.id,
        semester,
      });
      setSuccess("Course allocated successfully.");
      setCourseId("");
      setLecturerId("");
      await loadAllocations();
    } catch (err) {
      const resp = (err as { response?: { data?: Record<string, string[] | string> } }).response;
      const detail = resp?.data
        ? Object.entries(resp.data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ")
        : "Allocation failed. That course may already be allocated for this session/semester.";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1">Course Allocation</h4>
      <p className="text-muted">
        Assign lecturers to courses for {session ? session.name : "the current session"}
      </p>
      <Alert type="danger" message={error} />
      <Alert type="success" message={success} />

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">Allocate a Course</div>
        <div className="card-body">
          <form onSubmit={(e) => void handleSubmit(e)} className="row g-3 align-items-end">
            <div className="col-md-4">
              <label className="form-label">Course</label>
              <select
                className="form-select"
                value={courseId}
                onChange={(e) => setCourseId(e.target.value ? Number(e.target.value) : "")}
                required
              >
                <option value="">Select course…</option>
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>{c.code} — {c.title}</option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Lecturer</label>
              <select
                className="form-select"
                value={lecturerId}
                onChange={(e) => setLecturerId(e.target.value ? Number(e.target.value) : "")}
                required
              >
                <option value="">Select lecturer…</option>
                {lecturers.map((l) => (
                  <option key={l.id} value={l.id}>{l.full_name} ({l.staff_id})</option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <label className="form-label">Semester</label>
              <select
                className="form-select"
                value={semester}
                onChange={(e) => setSemester(e.target.value as Semester)}
              >
                <option value="FIRST">First</option>
                <option value="SECOND">Second</option>
              </select>
            </div>
            <div className="col-md-2">
              <button className="btn btn-primary w-100" type="submit" disabled={submitting || !session}>
                {submitting ? "…" : "Allocate"}
              </button>
            </div>
          </form>
          {!session && (
            <div className="text-danger small mt-2">No current academic session is set. Allocation is disabled.</div>
          )}
        </div>
      </div>

      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-semibold">
          Existing Allocations
          <span className="badge bg-primary ms-2">{allocations.length}</span>
        </div>
        {allocations.length === 0 ? (
          <div className="card-body text-center text-muted py-4">No allocations yet for this session.</div>
        ) : (
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Course</th>
                  <th>Lecturer</th>
                  <th>Session</th>
                  <th>Semester</th>
                </tr>
              </thead>
              <tbody>
                {allocations.map((a) => (
                  <tr key={a.id}>
                    <td><code>{a.course_code}</code> {a.course_title}</td>
                    <td>{a.lecturer_name}</td>
                    <td>{a.session_name}</td>
                    <td>{a.semester}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
