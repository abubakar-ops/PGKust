import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTimetable } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { TimetableEntry } from "../../types";

const DAY_ORDER = ["MON", "TUE", "WED", "THU", "FRI"];
const DAY_LABELS: Record<string, string> = {
  MON: "Monday", TUE: "Tuesday", WED: "Wednesday", THU: "Thursday", FRI: "Friday",
};

export default function LecturerTimetablePage() {
  const [entries, setEntries] = useState<TimetableEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getTimetable().then(({ data }) => setEntries(data))
      .catch(() => setError("Failed to load your timetable."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  const ordered = [...entries].sort((a, b) =>
    DAY_ORDER.indexOf(a.day) - DAY_ORDER.indexOf(b.day) ||
    a.start_time.localeCompare(b.start_time)
  );

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div><h4 className="fw-bold mb-1">My Timetable</h4><p className="text-muted mb-0">Classes assigned to you this session</p></div>
        <Link to="/lecturer/dashboard" className="btn btn-outline-secondary btn-sm">← Dashboard</Link>
      </div>
      {error && <div className="alert alert-danger">{error}</div>}
      <div className="card border-0 shadow-sm">
        {ordered.length === 0 ? <div className="card-body text-center text-muted py-5">No timetable entries found for your allocations.</div> : (
          <div className="table-responsive"><table className="table table-hover align-middle mb-0">
            <thead className="table-light"><tr><th>Day</th><th>Time</th><th>Course</th><th>Venue</th></tr></thead>
            <tbody>{ordered.map((entry) => {
              const a = entry.allocation_detail;
              return <tr key={entry.id}>
                <td className="fw-semibold">{DAY_LABELS[entry.day] ?? entry.day}</td>
                <td>{entry.start_time} – {entry.end_time}</td>
                <td><code>{a.course_code}</code><div>{a.course_title}</div></td>
                <td>{entry.venue || "—"}</td>
              </tr>;
            })}</tbody>
          </table></div>
        )}
      </div>
    </div>
  );
}
