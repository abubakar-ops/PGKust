import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminStudentReview, getAllStudents } from "../../api/auth";
import Alert from "../../components/Alert";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { StudentProfile, StudentReview } from "../../types";

const STATUS_OPTIONS = ["PENDING", "ACTIVE", "SUSPENDED", "GRADUATED"] as const;

function statusClass(status: string) {
  if (status === "ACTIVE") return "bg-success";
  if (status === "PENDING") return "bg-warning text-dark";
  if (status === "SUSPENDED") return "bg-danger";
  return "bg-secondary";
}

export default function AdminStudentReviewPage() {
  const [students, setStudents] = useState<StudentProfile[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [profile, setProfile] = useState<StudentReview | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  const [error, setError] = useState("");
  const [profileError, setProfileError] = useState("");
  const [profileErrorId, setProfileErrorId] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    const timeout = window.setTimeout(() => {
      void getAllStudents(statusFilter || undefined, search.trim())
        .then(({ data }) => {
          if (!active) return;
          setStudents(data);
          setError("");
          setSelectedId((current) =>
            current !== null && data.some((student) => student.id === current) ? current : null
          );
        })
        .catch(() => {
          if (active) setError("Could not load students. Please try again.");
        })
        .finally(() => {
          if (active) setListLoading(false);
        });
    }, search ? 250 : 0);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [search, statusFilter]);

  useEffect(() => {
    if (selectedId === null) return;
    let active = true;
    void getAdminStudentReview(selectedId)
      .then(({ data }) => {
        if (active) {
          setProfile(data);
          setProfileError("");
          setProfileErrorId(null);
        }
      })
      .catch(() => {
        if (active) {
          setProfileError("Could not load this student's profile. Please try again.");
          setProfileErrorId(selectedId);
        }
      })
      .finally(() => {
        if (active) setProfileLoading(false);
      });
    return () => { active = false; };
  }, [selectedId]);

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 className="fw-bold mb-1">Student Review Centre</h4>
          <p className="text-muted mb-0">Find a student and review their profile and available academic history.</p>
        </div>
        <div className="d-flex gap-2">
          <Link to="/admin/students/all" className="btn btn-outline-primary btn-sm">All Students</Link>
          <Link to="/admin/students" className="btn btn-outline-warning btn-sm">Pending Students</Link>
        </div>
      </div>

      <Alert message={error} />
      <div className="row g-4">
        <div className="col-lg-4">
          <div className="card border-0 shadow-sm">
            <div className="card-header bg-white fw-semibold">
              Search students <span className="badge bg-primary ms-2">{students.length}</span>
            </div>
            <div className="card-body">
              <label htmlFor="review-student-search" className="form-label">Name, email or matriculation number</label>
              <input
                id="review-student-search"
                className="form-control mb-3"
                type="search"
                value={search}
                onChange={(event) => { setListLoading(true); setSearch(event.target.value); }}
                placeholder="Start typing to search"
              />
              <label htmlFor="review-student-status" className="form-label">Account status</label>
              <select
                id="review-student-status"
                className="form-select mb-3"
                value={statusFilter}
                onChange={(event) => { setListLoading(true); setStatusFilter(event.target.value); }}
              >
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
              </select>

              {listLoading ? <LoadingSpinner text="Searching students…" /> : students.length === 0 ? (
                <div className="text-center text-muted py-4">No students match your search.</div>
              ) : (
                <div className="list-group list-group-flush">
                  {students.map((student) => (
                    <button
                      key={student.id}
                      type="button"
                      className={`list-group-item list-group-item-action ${student.id === selectedId ? "active" : ""}`}
                      aria-pressed={student.id === selectedId}
                      onClick={() => {
                        setProfileLoading(true);
                        setSelectedId(student.id);
                      }}
                    >
                      <div className="d-flex justify-content-between align-items-start gap-2">
                        <span className="fw-semibold">{student.full_name || `${student.first_name} ${student.last_name}`}</span>
                        <span className={`badge ${student.id === selectedId ? "bg-light text-dark" : statusClass(student.status)}`}>
                          {student.status}
                        </span>
                      </div>
                      <span className="small d-block">{student.matric_number}</span>
                      <span className="small d-block text-truncate">{student.email}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-lg-8">
          <Alert message={profileErrorId === selectedId ? profileError : ""} />
          {selectedId !== null && profileLoading
            ? <div className="card border-0 shadow-sm"><LoadingSpinner text="Loading student profile…" /></div>
            : selectedId === null ? (
              <div className="card border-0 shadow-sm">
                <div className="card-body text-center text-muted py-5">Select a student to view their profile.</div>
              </div>
            ) : !profile || profile.id !== selectedId ? (
              <div className="card border-0 shadow-sm">
                <div className="card-body text-center text-muted py-5">
                  {profileErrorId === selectedId ? "Student profile could not be loaded." : "Loading student profile…"}
                </div>
              </div>
            ) : (
              <>
                <div className="card border-0 shadow-sm mb-4">
                  <div className="card-header bg-white d-flex justify-content-between align-items-center">
                    <span className="fw-semibold">Student Profile</span>
                    <span className={`badge ${statusClass(profile.status)}`}>{profile.status}</span>
                  </div>
                  <div className="card-body">
                    <h5 className="fw-bold">{profile.full_name}</h5>
                    <dl className="row mb-0">
                      <dt className="col-sm-4">Student profile ID</dt><dd className="col-sm-8">{profile.id}</dd>
                      <dt className="col-sm-4">Matriculation number</dt><dd className="col-sm-8">{profile.matric_number}</dd>
                      <dt className="col-sm-4">Email</dt><dd className="col-sm-8">{profile.email}</dd>
                      <dt className="col-sm-4">Phone</dt><dd className="col-sm-8">{profile.phone_number || "Not provided"}</dd>
                      <dt className="col-sm-4">Programme</dt><dd className="col-sm-8">{profile.programme_display} ({profile.programme})</dd>
                      <dt className="col-sm-4">Degree type</dt><dd className="col-sm-8">{profile.programme === "PHD" ? "Doctor of Philosophy (PhD)" : "Master of Science (MSc)"}</dd>
                      <dt className="col-sm-4">Admission year</dt><dd className="col-sm-8">{profile.admission_year}</dd>
                      <dt className="col-sm-4">Supervisor</dt>
                      <dd className="col-sm-8">{profile.supervisor
                        ? `${profile.supervisor.full_name} (${profile.supervisor.staff_id})${profile.supervisor.specialization ? ` · ${profile.supervisor.specialization}` : ""}`
                        : "Not assigned"}</dd>
                      {profile.registration_note && <>
                        <dt className="col-sm-4">Registration note</dt><dd className="col-sm-8">{profile.registration_note}</dd>
                      </>}
                    </dl>
                    <div className="d-flex gap-2 mt-3">
                      <Link to="/admin/students/all" className="btn btn-sm btn-outline-primary">Edit in All Students</Link>
                      {profile.status === "PENDING" &&
                        <Link to="/admin/students" className="btn btn-sm btn-outline-warning">Review pending approval</Link>}
                    </div>
                  </div>
                </div>

                <div className="card border-0 shadow-sm mb-4">
                  <div className="card-header bg-white fw-semibold">Course Enrollments</div>
                  {profile.enrollments.length === 0 ? <div className="card-body text-muted">No enrollment records.</div> :
                    <div className="table-responsive"><table className="table table-hover align-middle mb-0">
                      <thead className="table-light"><tr><th>Course</th><th>Session / Semester</th><th>Enrollment</th><th>Result</th></tr></thead>
                      <tbody>{profile.enrollments.map((enrollment) => <tr key={enrollment.id}>
                        <td><code>{enrollment.course_code}</code><div>{enrollment.course_title}</div></td>
                        <td>{enrollment.session_name}<div>{enrollment.semester}</div></td>
                        <td>{enrollment.status}</td>
                        <td>{enrollment.result
                          ? `${enrollment.result.grade} · ${enrollment.result.score}`
                          : "Not available"}</td>
                      </tr>)}</tbody>
                    </table></div>}
                </div>

                <div className="card border-0 shadow-sm mb-4">
                  <div className="card-header bg-white fw-semibold">GPA / CGPA</div>
                  <div className="card-body">
                    {profile.cumulative_gpa && <p className="mb-2">
                      <strong>CGPA:</strong> {profile.cumulative_gpa.cgpa} · {profile.cumulative_gpa.classification}
                    </p>}
                    {profile.semester_gpas.length === 0 && !profile.cumulative_gpa
                      ? <div className="text-muted">No GPA records available.</div>
                      : profile.semester_gpas.length > 0 && <div className="table-responsive"><table className="table table-sm mb-0">
                        <thead><tr><th>Session</th><th>Semester</th><th>GPA</th><th>Credits earned</th></tr></thead>
                        <tbody>{profile.semester_gpas.map((gpa) => <tr key={gpa.id}>
                          <td>{gpa.session_name}</td><td>{gpa.semester}</td><td>{gpa.gpa}</td><td>{gpa.credit_units_earned}</td>
                        </tr>)}</tbody>
                      </table></div>}
                  </div>
                </div>

                <div className="card border-0 shadow-sm">
                  <div className="card-header bg-white fw-semibold">Annual Progress Reports</div>
                  {profile.annual_progress_reports.length === 0
                    ? <div className="card-body text-muted">No annual progress report records.</div>
                    : <div className="table-responsive"><table className="table table-hover align-middle mb-0">
                      <thead className="table-light"><tr><th>Session</th><th>Year of study</th><th>Status</th><th>Progression cleared</th></tr></thead>
                      <tbody>{profile.annual_progress_reports.map((report) => <tr key={report.id}>
                        <td>{report.session_name}</td><td>{report.year_of_study}</td><td>{report.status}</td>
                        <td>{report.progression_cleared ? "Yes" : "No"}</td>
                      </tr>)}</tbody>
                    </table></div>}
                </div>
              </>
            )}
        </div>
      </div>
    </div>
  );
}
