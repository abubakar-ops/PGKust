import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  adminCreateTimetable, adminDeleteTimetable, adminGetAllocations,
  adminGetTimetable, adminUpdateTimetable,
} from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import Alert from "../../components/Alert";
import type { CourseAllocation, TimetableEntry } from "../../types";

const DAYS = [
  ["MON", "Monday"], ["TUE", "Tuesday"], ["WED", "Wednesday"],
  ["THU", "Thursday"], ["FRI", "Friday"],
] as const;
const DAY_LABELS: Record<string, string> = Object.fromEntries(DAYS);

function errorMessage(err: unknown) {
  const data = (err as { response?: { data?: Record<string, unknown> } }).response?.data;
  if (!data) return "Request failed. Please try again.";
  return Object.entries(data).map(([key, value]) =>
    `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`
  ).join(" | ");
}

export default function AdminTimetablePage() {
  const [entries, setEntries] = useState<TimetableEntry[]>([]);
  const [allocations, setAllocations] = useState<CourseAllocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editing, setEditing] = useState<TimetableEntry | null>(null);
  const [allocation, setAllocation] = useState<number | "">("");
  const [day, setDay] = useState("MON");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [venue, setVenue] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const [{ data: timetable }, { data: allocationList }] = await Promise.all([
      adminGetTimetable(), adminGetAllocations(),
    ]);
    setEntries(timetable);
    setAllocations(allocationList);
  }, []);

  useEffect(() => { load().catch(() => setError("Failed to load timetable data.")).finally(() => setLoading(false)); }, [load]);

  function resetForm() {
    setEditing(null); setAllocation(""); setDay("MON"); setStartTime(""); setEndTime(""); setVenue("");
  }
  function beginEdit(entry: TimetableEntry) {
    setEditing(entry); setAllocation(entry.allocation); setDay(entry.day);
    setStartTime(entry.start_time); setEndTime(entry.end_time); setVenue(entry.venue);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true); setError(""); setSuccess("");
    try {
      const payload = { allocation, day, start_time: startTime, end_time: endTime, venue };
      if (editing) await adminUpdateTimetable(editing.id, payload);
      else await adminCreateTimetable(payload);
      await load(); setSuccess(editing ? "Timetable entry updated." : "Timetable entry created."); resetForm();
    } catch (err: unknown) { setError(errorMessage(err)); }
    finally { setSaving(false); }
  }
  async function remove(entry: TimetableEntry) {
    if (!window.confirm(`Delete the timetable entry for ${entry.allocation_detail.course_code}?`)) return;
    setError(""); setSuccess("");
    try { await adminDeleteTimetable(entry.id); setEntries((prev) => prev.filter((item) => item.id !== entry.id)); setSuccess("Timetable entry deleted."); }
    catch (err: unknown) { setError(errorMessage(err)); }
  }

  if (loading) return <LoadingSpinner />;
  return <div className="container py-4">
    <div className="d-flex justify-content-between align-items-center mb-3">
      <div><h4 className="fw-bold mb-1">Timetable Management</h4><p className="text-muted mb-0">Manage current course schedules</p></div>
      <Link to="/admin/dashboard" className="btn btn-outline-secondary btn-sm">← Dashboard</Link>
    </div>
    <Alert type="danger" message={error} /><Alert type="success" message={success} />
    <div className="card border-0 shadow-sm mb-4">
      <div className="card-header bg-white fw-semibold">{editing ? "Edit Timetable Entry" : "Add Timetable Entry"}</div>
      <div className="card-body"><form onSubmit={(e) => void submit(e)} className="row g-3 align-items-end">
        <div className="col-lg-4"><label className="form-label">Course allocation</label>
          <select className="form-select" value={allocation} onChange={(e) => setAllocation(e.target.value ? Number(e.target.value) : "")} required>
            <option value="">Select allocation…</option>
            {allocations.map((a) => <option key={a.id} value={a.id}>{a.course_code} — {a.course_title} · {a.lecturer_name} · {a.session_name} · {a.semester}</option>)}
          </select>
        </div>
        <div className="col-sm-3 col-lg-2"><label className="form-label">Day</label><select className="form-select" value={day} onChange={(e) => setDay(e.target.value)}>{DAYS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
        <div className="col-sm-3 col-lg-2"><label className="form-label">Start</label><input className="form-control" type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} required /></div>
        <div className="col-sm-3 col-lg-2"><label className="form-label">End</label><input className="form-control" type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} required /></div>
        <div className="col-sm-3 col-lg-2"><label className="form-label">Venue</label><input className="form-control" value={venue} onChange={(e) => setVenue(e.target.value)} required /></div>
        <div className="col-12 d-flex gap-2"><button className="btn btn-primary" disabled={saving}>{saving ? "Saving…" : editing ? "Save Changes" : "Add Timetable"}</button>{editing && <button type="button" className="btn btn-outline-secondary" onClick={resetForm}>Cancel</button>}</div>
      </form></div>
    </div>
    <div className="card border-0 shadow-sm"><div className="card-header bg-white fw-semibold">Timetable Entries <span className="badge bg-primary ms-2">{entries.length}</span></div>
      {entries.length === 0 ? <div className="card-body text-center text-muted py-5">No timetable entries yet.</div> :
        <div className="table-responsive"><table className="table table-hover align-middle mb-0"><thead className="table-light"><tr><th>Course</th><th>Lecturer</th><th>Programme / Session</th><th>Day</th><th>Time</th><th>Venue</th><th /></tr></thead>
          <tbody>{entries.map((entry) => { const a = entry.allocation_detail; return <tr key={entry.id}><td><code>{a.course_code}</code><div>{a.course_title}</div></td><td>{a.lecturer_name}</td><td>{a.programme_name}<div className="small text-muted">{a.session_name} · {a.semester}</div></td><td>{DAY_LABELS[entry.day] ?? entry.day}</td><td>{entry.start_time} – {entry.end_time}</td><td>{entry.venue}</td><td className="text-end text-nowrap"><button className="btn btn-sm btn-outline-primary me-1" onClick={() => beginEdit(entry)}>Edit</button><button className="btn btn-sm btn-outline-danger" onClick={() => void remove(entry)}>Delete</button></td></tr>; })}</tbody>
        </table></div>}
    </div>
  </div>;
}
