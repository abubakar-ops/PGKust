import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  adminCreateCourse, adminCreateProgramme, adminCreateSession,
  adminDeleteCourse, adminDeleteProgramme, adminDeleteSession,
  adminGetCourses, adminGetProgrammes, adminGetSessions,
  adminUpdateCourse, adminUpdateProgramme, adminUpdateSession,
} from "../../api/courses";
import Alert from "../../components/Alert";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { AcademicSession, Course, Programme, ProgrammeType, Semester } from "../../types";

type Section = "sessions" | "programmes" | "courses";

const SECTION_LABELS: Record<Section, string> = {
  sessions: "Academic Sessions",
  programmes: "Programmes",
  courses: "Courses",
};

const emptySession = () => ({
  name: "", start_date: "", end_date: "", department_fee: "", is_current: false,
});
const emptyProgramme = () => ({
  name: "", programme_type: "MSC" as ProgrammeType, duration_years: "2", description: "",
});
const emptyCourse = () => ({
  code: "", title: "", credit_units: "1", semester: "FIRST" as Semester,
  programme: "", is_elective: false, is_active: true, description: "",
});

function getErrorMessage(error: unknown): string {
  const responseData = (error as { response?: { data?: unknown } }).response?.data;
  if (responseData === undefined) return "Request failed. Please try again.";
  if (typeof responseData === "string") return responseData;

  const data = responseData && typeof responseData === "object" && "errors" in responseData
    ? (responseData as { errors: unknown }).errors
    : responseData;
  const formatMessages = (value: unknown): string => {
    if (Array.isArray(value)) return value.map(formatMessages).filter(Boolean).join(", ");
    if (value && typeof value === "object") {
      return Object.entries(value).map(([field, nested]) => `${field}: ${formatMessages(nested)}`).join(" | ");
    }
    return String(value);
  };

  if (data && typeof data === "object") {
    return Object.entries(data).map(([field, value]) => {
      const messages = formatMessages(value);
      return field === "detail" ? messages : `${field}: ${messages}`;
    }).join(" | ");
  }
  return typeof data === "string" ? data : "Request failed. Please check the submitted information.";
}

export default function AdminAcademicPage() {
  const [section, setSection] = useState<Section>("sessions");
  const [sessions, setSessions] = useState<AcademicSession[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [sessionForm, setSessionForm] = useState(emptySession);
  const [programmeForm, setProgrammeForm] = useState(emptyProgramme);
  const [courseForm, setCourseForm] = useState(emptyCourse);

  const fetchAcademicRecords = useCallback(async () => Promise.all([
      adminGetSessions(), adminGetProgrammes(), adminGetCourses(),
  ]), []);

  const load = useCallback(async () => {
    const [sessionResponse, programmeResponse, courseResponse] = await fetchAcademicRecords();
    setSessions(sessionResponse.data);
    setProgrammes(programmeResponse.data);
    setCourses(courseResponse.data);
  }, [fetchAcademicRecords]);

  useEffect(() => {
    let active = true;
    void fetchAcademicRecords()
      .then(([sessionResponse, programmeResponse, courseResponse]) => {
        if (!active) return;
        setSessions(sessionResponse.data);
        setProgrammes(programmeResponse.data);
        setCourses(courseResponse.data);
      })
      .catch((loadError: unknown) => {
        if (active) setError(getErrorMessage(loadError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [fetchAcademicRecords]);

  function resetForm() {
    setEditingId(null);
    setSessionForm(emptySession());
    setProgrammeForm(emptyProgramme());
    setCourseForm(emptyCourse());
  }

  function changeSection(nextSection: Section) {
    setSection(nextSection);
    setError("");
    setSuccess("");
    resetForm();
  }

  function editSession(session: AcademicSession) {
    setEditingId(session.id);
    setSessionForm({
      name: session.name,
      start_date: session.start_date,
      end_date: session.end_date,
      department_fee: session.department_fee,
      is_current: session.is_current,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function editProgramme(programme: Programme) {
    setEditingId(programme.id);
    setProgrammeForm({
      name: programme.name,
      programme_type: programme.programme_type,
      duration_years: String(programme.duration_years),
      description: programme.description,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function editCourse(course: Course) {
    setEditingId(course.id);
    setCourseForm({
      code: course.code,
      title: course.title,
      credit_units: String(course.credit_units),
      semester: course.semester,
      programme: String(course.programme),
      is_elective: course.is_elective,
      is_active: course.is_active,
      description: course.description,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      if (section === "sessions") {
        const payload = sessionForm;
        if (editingId !== null) await adminUpdateSession(editingId, payload);
        else await adminCreateSession(payload);
      } else if (section === "programmes") {
        const payload = {
          ...programmeForm,
          duration_years: Number(programmeForm.duration_years),
        };
        if (editingId !== null) await adminUpdateProgramme(editingId, payload);
        else await adminCreateProgramme(payload);
      } else {
        const payload = {
          ...courseForm,
          code: courseForm.code.trim().toUpperCase(),
          credit_units: Number(courseForm.credit_units),
          programme: Number(courseForm.programme),
        };
        if (editingId !== null) await adminUpdateCourse(editingId, payload);
        else await adminCreateCourse(payload);
      }
      await load();
      setSuccess(`${SECTION_LABELS[section].replace(/s$/, "")} ${editingId !== null ? "updated" : "created"} successfully.`);
      resetForm();
    } catch (saveError: unknown) {
      setError(getErrorMessage(saveError));
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: number, displayName: string) {
    if (!window.confirm(`Delete "${displayName}"? This cannot be undone.`)) return;
    setError("");
    setSuccess("");
    setDeletingId(id);
    try {
      if (section === "sessions") await adminDeleteSession(id);
      else if (section === "programmes") await adminDeleteProgramme(id);
      else await adminDeleteCourse(id);
      await load();
      setSuccess(`${SECTION_LABELS[section].replace(/s$/, "")} deleted successfully.`);
      if (editingId === id) resetForm();
    } catch (deleteError: unknown) {
      setError(getErrorMessage(deleteError));
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) return <LoadingSpinner text="Loading academic records…" />;

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 className="fw-bold mb-1">Academic Setup</h4>
          <p className="text-muted mb-0">Manage academic sessions, programmes and course definitions.</p>
        </div>
        <Link to="/admin/dashboard" className="btn btn-outline-secondary btn-sm">← Dashboard</Link>
      </div>
      <Alert type="danger" message={error} />
      <Alert type="success" message={success} />

      <ul className="nav nav-tabs mb-4" role="tablist" aria-label="Academic record types">
        {(Object.keys(SECTION_LABELS) as Section[]).map((key) => (
          <li className="nav-item" key={key} role="presentation">
            <button
              type="button"
              className={`nav-link ${section === key ? "active" : ""}`}
              aria-current={section === key ? "page" : undefined}
              onClick={() => changeSection(key)}
            >
              {SECTION_LABELS[key]}
            </button>
          </li>
        ))}
      </ul>

      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white fw-semibold">
          {editingId !== null ? `Edit ${SECTION_LABELS[section].replace(/s$/, "")}` : `Add ${SECTION_LABELS[section].replace(/s$/, "")}`}
        </div>
        <div className="card-body">
          <form onSubmit={(event) => void submit(event)} className="row g-3 align-items-end">
            {section === "sessions" && <>
              <div className="col-md-4">
                <label className="form-label" htmlFor="session-name">Session name</label>
                <input id="session-name" className="form-control" maxLength={20} placeholder="2026/2027"
                  value={sessionForm.name} onChange={(event) => setSessionForm({ ...sessionForm, name: event.target.value })} required />
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="session-start">Start date</label>
                <input id="session-start" className="form-control" type="date"
                  value={sessionForm.start_date} onChange={(event) => setSessionForm({ ...sessionForm, start_date: event.target.value })} required />
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="session-end">End date</label>
                <input id="session-end" className="form-control" type="date" min={sessionForm.start_date || undefined}
                  value={sessionForm.end_date} onChange={(event) => setSessionForm({ ...sessionForm, end_date: event.target.value })} required />
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="session-fee">Department fee</label>
                <input id="session-fee" className="form-control" type="number" min="0.01" step="0.01"
                  value={sessionForm.department_fee}
                  onChange={(event) => setSessionForm({ ...sessionForm, department_fee: event.target.value })} required />
              </div>
              <div className="col-md-2 form-check ms-2">
                <input id="session-current" className="form-check-input" type="checkbox"
                  checked={sessionForm.is_current} onChange={(event) => setSessionForm({ ...sessionForm, is_current: event.target.checked })} />
                <label className="form-check-label" htmlFor="session-current">Current session</label>
              </div>
            </>}

            {section === "programmes" && <>
              <div className="col-md-5">
                <label className="form-label" htmlFor="programme-name">Programme name</label>
                <input id="programme-name" className="form-control" maxLength={100}
                  value={programmeForm.name} onChange={(event) => setProgrammeForm({ ...programmeForm, name: event.target.value })} required />
              </div>
              <div className="col-md-3">
                <label className="form-label" htmlFor="programme-type">Programme type</label>
                <select id="programme-type" className="form-select" value={programmeForm.programme_type}
                  onChange={(event) => setProgrammeForm({ ...programmeForm, programme_type: event.target.value as ProgrammeType })}>
                  <option value="MSC">Master of Science (MSc)</option>
                  <option value="PHD">Doctor of Philosophy (PhD)</option>
                </select>
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="programme-duration">Duration (years)</label>
                <input id="programme-duration" className="form-control" type="number" min="1" max="32767"
                  value={programmeForm.duration_years} onChange={(event) => setProgrammeForm({ ...programmeForm, duration_years: event.target.value })} required />
              </div>
              <div className="col-12">
                <label className="form-label" htmlFor="programme-description">Description</label>
                <textarea id="programme-description" className="form-control" rows={2}
                  value={programmeForm.description} onChange={(event) => setProgrammeForm({ ...programmeForm, description: event.target.value })} />
              </div>
            </>}

            {section === "courses" && <>
              <div className="col-md-2">
                <label className="form-label" htmlFor="course-code">Course code</label>
                <input id="course-code" className="form-control" maxLength={10}
                  value={courseForm.code} onChange={(event) => setCourseForm({ ...courseForm, code: event.target.value })} required />
              </div>
              <div className="col-md-4">
                <label className="form-label" htmlFor="course-title">Title</label>
                <input id="course-title" className="form-control" maxLength={150}
                  value={courseForm.title} onChange={(event) => setCourseForm({ ...courseForm, title: event.target.value })} required />
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="course-credits">Credit units</label>
                <input id="course-credits" className="form-control" type="number" min="1" max="32767"
                  value={courseForm.credit_units} onChange={(event) => setCourseForm({ ...courseForm, credit_units: event.target.value })} required />
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="course-semester">Semester</label>
                <select id="course-semester" className="form-select" value={courseForm.semester}
                  onChange={(event) => setCourseForm({ ...courseForm, semester: event.target.value as Semester })}>
                  <option value="FIRST">First</option>
                  <option value="SECOND">Second</option>
                </select>
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="course-programme">Programme</label>
                <select id="course-programme" className="form-select" value={courseForm.programme}
                  onChange={(event) => setCourseForm({ ...courseForm, programme: event.target.value })} required>
                  <option value="">Select…</option>
                  {programmes.map((programme) => (
                    <option key={programme.id} value={programme.id}>{programme.name} ({programme.programme_type})</option>
                  ))}
                </select>
              </div>
              <div className="col-12">
                <label className="form-label" htmlFor="course-description">Description</label>
                <textarea id="course-description" className="form-control" rows={2}
                  value={courseForm.description} onChange={(event) => setCourseForm({ ...courseForm, description: event.target.value })} />
              </div>
              <div className="col-auto form-check ms-2">
                <input id="course-elective" className="form-check-input" type="checkbox" checked={courseForm.is_elective}
                  onChange={(event) => setCourseForm({ ...courseForm, is_elective: event.target.checked })} />
                <label className="form-check-label" htmlFor="course-elective">Elective</label>
              </div>
              <div className="col-auto form-check">
                <input id="course-active" className="form-check-input" type="checkbox" checked={courseForm.is_active}
                  onChange={(event) => setCourseForm({ ...courseForm, is_active: event.target.checked })} />
                <label className="form-check-label" htmlFor="course-active">Active</label>
              </div>
              {programmes.length === 0 && <div className="col-12 small text-danger">Create a programme before adding a course.</div>}
            </>}

            <div className="col-12 d-flex gap-2">
              <button className="btn btn-primary" type="submit" disabled={saving || (section === "courses" && programmes.length === 0)}>
                {saving ? "Saving…" : editingId !== null ? "Save Changes" : "Create"}
              </button>
              {editingId !== null && <button className="btn btn-outline-secondary" type="button" onClick={resetForm}>Cancel</button>}
            </div>
          </form>
        </div>
      </div>

      {section === "sessions" && (
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white fw-semibold">Academic Sessions <span className="badge bg-primary ms-2">{sessions.length}</span></div>
          {sessions.length === 0 ? <div className="card-body text-center text-muted py-5">No academic sessions yet.</div> :
            <div className="table-responsive"><table className="table table-hover align-middle mb-0">
              <thead className="table-light"><tr><th>Session</th><th>Dates</th><th>Department fee</th><th>Status</th><th /></tr></thead>
              <tbody>{sessions.map((item) => <tr key={item.id}>
                <td>{item.name}</td><td>{item.start_date} – {item.end_date}</td><td>₦{item.department_fee}</td>
                <td>{item.is_current ? <span className="badge bg-success">Current</span> : "—"}</td>
                <td className="text-end text-nowrap">
                  <button className="btn btn-sm btn-outline-primary me-1" onClick={() => editSession(item)}>Edit</button>
                  <button className="btn btn-sm btn-outline-danger" disabled={deletingId === item.id}
                    onClick={() => void remove(item.id, item.name)}>{deletingId === item.id ? "Deleting…" : "Delete"}</button>
                </td>
              </tr>)}</tbody>
            </table></div>}
        </div>
      )}

      {section === "programmes" && (
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white fw-semibold">Programmes <span className="badge bg-primary ms-2">{programmes.length}</span></div>
          {programmes.length === 0 ? <div className="card-body text-center text-muted py-5">No programmes yet.</div> :
            <div className="table-responsive"><table className="table table-hover align-middle mb-0">
              <thead className="table-light"><tr><th>Name</th><th>Type</th><th>Duration</th><th>Description</th><th /></tr></thead>
              <tbody>{programmes.map((item) => <tr key={item.id}>
                <td>{item.name}</td><td>{item.programme_type}</td><td>{item.duration_years} years</td>
                <td>{item.description || "—"}</td>
                <td className="text-end text-nowrap">
                  <button className="btn btn-sm btn-outline-primary me-1" onClick={() => editProgramme(item)}>Edit</button>
                  <button className="btn btn-sm btn-outline-danger" disabled={deletingId === item.id}
                    onClick={() => void remove(item.id, item.name)}>{deletingId === item.id ? "Deleting…" : "Delete"}</button>
                </td>
              </tr>)}</tbody>
            </table></div>}
        </div>
      )}

      {section === "courses" && (
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white fw-semibold">Course Definitions <span className="badge bg-primary ms-2">{courses.length}</span></div>
          {courses.length === 0 ? <div className="card-body text-center text-muted py-5">No course definitions yet.</div> :
            <div className="table-responsive"><table className="table table-hover align-middle mb-0">
              <thead className="table-light"><tr><th>Code</th><th>Title</th><th>Programme</th><th>Semester</th><th>Credits</th><th>Description</th><th>Status</th><th /></tr></thead>
              <tbody>{courses.map((item) => <tr key={item.id}>
                <td><code>{item.code}</code></td><td>{item.title}</td><td>{item.programme_name}</td>
                <td>{item.semester}</td><td>{item.credit_units}</td><td>{item.description || "—"}</td>
                <td>{item.is_active ? "Active" : "Inactive"}{item.is_elective ? " · Elective" : ""}</td>
                <td className="text-end text-nowrap">
                  <button className="btn btn-sm btn-outline-primary me-1" onClick={() => editCourse(item)}>Edit</button>
                  <button className="btn btn-sm btn-outline-danger" disabled={deletingId === item.id}
                    onClick={() => void remove(item.id, item.code)}>{deletingId === item.id ? "Deleting…" : "Delete"}</button>
                </td>
              </tr>)}</tbody>
            </table></div>}
        </div>
      )}
    </div>
  );
}
