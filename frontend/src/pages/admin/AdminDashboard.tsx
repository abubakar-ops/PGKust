import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import LoadingSpinner from "../../components/LoadingSpinner";

interface DashboardStats {
  students: number;
  lecturers: number;
  batches: number;
  fees: number;
  aprs: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([
      api.get<unknown[]>("/accounts/admin/students/pending/").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/accounts/admin/lecturers/pending/").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/results/batches/?status=PENDING").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/fees/admin/list/?status=PENDING").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/reports/apr/?status=SUBMITTED").then(({ data }) => data.length).catch(() => 0),
    ]).then(([students, lecturers, batches, fees, aprs]) => {
      setStats({ students, lecturers, batches, fees, aprs });
    }).finally(() => setLoading(false));
  }, []);

  if (loading || !stats) return <LoadingSpinner />;

  const cards: { label: string; count: number; to: string; color: string }[] = [
    { label: "Pending Students",  count: stats.students,  to: "/admin/students",  color: "warning" },
    { label: "Pending Lecturers", count: stats.lecturers, to: "/admin/lecturers", color: "info" },
    { label: "Result Batches",    count: stats.batches,   to: "/admin/results",   color: "primary" },
    { label: "Fee Approvals",     count: stats.fees,      to: "/admin/fees",      color: "danger" },
    { label: "APR Reviews (PhD)", count: stats.aprs,      to: "/admin/apr",       color: "secondary" },
  ];

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1">Admin Dashboard</h4>
      <p className="text-muted">Pending approvals overview</p>
      <div className="row g-3 mb-4">
        {cards.map(({ label, count, to, color }) => (
          <div key={label} className="col-md-4 col-lg">
            <Link to={to} className="text-decoration-none">
              <div className={`card border-0 shadow-sm border-start border-4 border-${color} h-100`}>
                <div className="card-body">
                  <p className="text-muted small mb-1">{label}</p>
                  <span className={`fs-2 fw-bold text-${color}`}>{count}</span>
                </div>
              </div>
            </Link>
          </div>
        ))}
      </div>
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-bold">Quick Actions</div>
        <div className="card-body d-flex flex-wrap gap-2">
          <Link to="/admin/students" className="btn btn-outline-warning btn-sm">Review Students</Link>
          <Link to="/admin/results"  className="btn btn-outline-primary btn-sm">Approve Results</Link>
          <Link to="/admin/fees"     className="btn btn-outline-danger btn-sm">Approve Fees</Link>
          <Link to="/admin/apr"      className="btn btn-outline-secondary btn-sm">Review APRs</Link>
          <Link to="/admin/courses"  className="btn btn-outline-info btn-sm">Manage Courses</Link>
        </div>
      </div>
    </div>
  );
}
