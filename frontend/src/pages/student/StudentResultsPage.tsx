import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMyResults, getGPA } from "../../api/results";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { Result, GPAResponse, SemesterGPA } from "../../types";

const SEMESTER_LABEL: Record<string, string> = {
  FIRST: "First Semester",
  SECOND: "Second Semester",
};

function semesterKey(sessionName: string, semester: string) {
  return `${sessionName}|${semester}`;
}

function classificationBadge(classification: string) {
  const map: Record<string, string> = {
    Distinction: "success",
    Merit: "primary",
    Pass: "warning",
    Fail: "danger",
  };
  return map[classification] ?? "secondary";
}

/** Single-hue progression meter: GPA on the fixed 0–5 scale. */
function GpaMeter({ gpa }: { gpa: number }) {
  const pct = Math.max(0, Math.min(100, (gpa / 5) * 100));
  return (
    <div
      className="progress"
      style={{ height: 10 }}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={5}
      aria-valuenow={gpa}
      aria-label={`GPA ${gpa.toFixed(2)} out of 5.00`}
    >
      <div className="progress-bar bg-primary" style={{ width: `${pct}%` }} />
    </div>
  );
}

function TrendArrow({ current, previous }: { current: number; previous: number | null }) {
  if (previous === null) return null;
  const diff = current - previous;
  if (Math.abs(diff) < 0.005) return <span className="text-muted small ms-2">— steady</span>;
  return diff > 0 ? (
    <span className="text-success small ms-2">▲ +{diff.toFixed(2)}</span>
  ) : (
    <span className="text-danger small ms-2">▼ {diff.toFixed(2)}</span>
  );
}

export default function StudentResultsPage() {
  const [results, setResults] = useState<Result[]>([]);
  const [gpaData, setGpaData] = useState<GPAResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getMyResults().then(({ data }) => setResults(data)),
      getGPA().then(({ data }) => setGpaData(data)),
    ])
      .catch(() => setError("Failed to load your results."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return (
    <div className="container py-4">
      <div className="alert alert-danger">{error}</div>
      <Link to="/student/dashboard" className="btn btn-outline-secondary">← Back to Dashboard</Link>
    </div>
  );

  const cumulative = gpaData?.cumulative ?? null;
  const semesterGpas: SemesterGPA[] = gpaData?.semester_gpas ?? [];

  // group course results per semester, in the same order as the GPA progression
  const grouped = new Map<string, Result[]>();
  for (const r of results) {
    const key = semesterKey(r.session_name, r.semester);
    grouped.set(key, [...(grouped.get(key) ?? []), r]);
  }

  const cgpa = cumulative ? Number(cumulative.cgpa) : null;

  return (
    <div className="container py-4" style={{ maxWidth: 900 }}>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="fw-bold mb-0">Academic Progression</h4>
          <p className="text-muted small mb-0">
            Approved results only — semester by semester, with GPA and CGPA
          </p>
        </div>
        <Link to="/student/dashboard" className="btn btn-outline-secondary btn-sm">← Dashboard</Link>
      </div>

      {results.length === 0 ? (
        <div className="alert alert-info">
          No approved results yet. Results appear here after the PG Coordinator publishes them.
        </div>
      ) : (
        <>
          {/* ── CGPA hero ─────────────────────────────────────────────── */}
          {cumulative && cgpa !== null && (
            <div className="card border-0 shadow-sm mb-4">
              <div className="card-body">
                <div className="row text-center align-items-center g-3">
                  <div className="col-md-4">
                    <div className="text-muted small text-uppercase">Cumulative GPA</div>
                    <div className="display-4 fw-bold">{cgpa.toFixed(2)}</div>
                    <div className="text-muted small">of 5.00</div>
                  </div>
                  <div className="col-md-3">
                    <div className="text-muted small text-uppercase mb-1">Classification</div>
                    <span className={`badge fs-6 bg-${classificationBadge(cumulative.classification)}`}>
                      {cumulative.classification}
                    </span>
                  </div>
                  <div className="col-md-2">
                    <div className="text-muted small text-uppercase mb-1">Credit Units</div>
                    <div className="fs-4 fw-semibold">{cumulative.total_credit_units_earned}</div>
                  </div>
                  <div className="col-md-3">
                    <div className="text-muted small text-uppercase mb-1">Graduation Standing</div>
                    {cgpa >= 2.5 ? (
                      <span className="badge bg-success fs-6">✓ On Track (≥ 2.50)</span>
                    ) : (
                      <span className="badge bg-danger fs-6">Below 2.50 minimum</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Semester progression ─────────────────────────────────── */}
          <div className="card border-0 shadow-sm mb-4">
            <div className="card-header bg-white fw-semibold">Semester Progression</div>
            <div className="card-body">
              {semesterGpas.map((sg, i) => {
                const gpa = Number(sg.gpa);
                const prev = i > 0 ? Number(semesterGpas[i - 1].gpa) : null;
                return (
                  <div key={sg.id} className={i > 0 ? "mt-3" : ""}>
                    <div className="d-flex justify-content-between align-items-baseline mb-1">
                      <span className="fw-semibold">
                        {sg.session_name} · {SEMESTER_LABEL[sg.semester] ?? sg.semester}
                      </span>
                      <span>
                        <span className="fw-bold">{gpa.toFixed(2)}</span>
                        <span className="text-muted small"> / 5.00</span>
                        <TrendArrow current={gpa} previous={prev} />
                      </span>
                    </div>
                    <GpaMeter gpa={gpa} />
                    <div className="text-muted small mt-1">{sg.credit_units_earned} credit units</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Per-semester course results ──────────────────────────── */}
          {semesterGpas.map((sg) => {
            const key = semesterKey(sg.session_name, sg.semester);
            const rows = grouped.get(key) ?? [];
            if (rows.length === 0) return null;
            return (
              <div key={key} className="card border-0 shadow-sm mb-4">
                <div className="card-header bg-white fw-semibold d-flex justify-content-between">
                  <span>{sg.session_name} · {SEMESTER_LABEL[sg.semester] ?? sg.semester}</span>
                  <span className="text-muted">GPA: {Number(sg.gpa).toFixed(2)}</span>
                </div>
                <div className="table-responsive">
                  <table className="table table-sm align-middle mb-0">
                    <thead className="table-light">
                      <tr>
                        <th>Code</th>
                        <th>Course Title</th>
                        <th className="text-center">CU</th>
                        <th className="text-center">Score</th>
                        <th className="text-center">Grade</th>
                        <th className="text-center">Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r) => (
                        <tr key={r.id}>
                          <td><code>{r.course_code}</code></td>
                          <td>{r.course_title}</td>
                          <td className="text-center">{r.credit_units}</td>
                          <td className="text-center">{Number(r.score).toFixed(0)}</td>
                          <td className="text-center">
                            <span className={`badge badge-grade-${r.grade}`}>{r.grade}</span>
                          </td>
                          <td className="text-center">{r.grade_point}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
