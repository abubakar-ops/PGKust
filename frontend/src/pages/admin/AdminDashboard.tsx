import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../../api/client";
import { getAdminDashboardStats } from "../../api/auth";
import LoadingSpinner from "../../components/LoadingSpinner";

interface DashboardStats {
  totalStudents: number;
  totalLecturers: number;
  totalCourses: number;
  totalEnrollments: number;
  pendingEnrollments: number;
  pendingStudents: number;
  pendingLecturers: number;
  batches: number;
  fees: number;
  aprs: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([
      getAdminDashboardStats().then(({ data }) => data),
      api.get<unknown[]>("/accounts/admin/students/pending/").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/accounts/admin/lecturers/pending/").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/results/batches/?status=PENDING").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/fees/admin/list/?status=PENDING").then(({ data }) => data.length).catch(() => 0),
      api.get<unknown[]>("/reports/apr/?status=SUBMITTED").then(({ data }) => data.length).catch(() => 0),
    ]).then(([overview, pendingStudents, pendingLecturers, batches, fees, aprs]) => {
      setStats({
        totalStudents: overview.total_students,
        totalLecturers: overview.total_lecturers,
        totalCourses: overview.total_courses,
        totalEnrollments: overview.total_enrollments,
        pendingEnrollments: overview.pending_enrollments,
        pendingStudents,
        pendingLecturers,
        batches,
        fees,
        aprs,
      });
    }).finally(() => setLoading(false));
  }, []);

  if (loading || !stats) return <LoadingSpinner />;

  const overviewCards: { label: string; count: number; color: string }[] = [
    { label: "Total Students",    count: stats.totalStudents,    color: "primary" },
    { label: "Total Lecturers",   count: stats.totalLecturers,   color: "info" },
    { label: "Total Courses",     count: stats.totalCourses,     color: "success" },
    { label: "Total Enrollments", count: stats.totalEnrollments, color: "secondary" },
  ];

  const approvalCards: { label: string; count: number; to: string; color: string }[] = [
    { label: "Pending Students",    count: stats.pendingStudents,    to: "/admin/students",     color: "warning" },
    { label: "Pending Lecturers",   count: stats.pendingLecturers,   to: "/admin/lecturers",    color: "info" },
    { label: "Pending Enrollments", count: stats.pendingEnrollments, to: "/admin/enrollments",  color: "warning" },
    { label: "Result Batches",      count: stats.batches,             to: "/admin/results",      color: "primary" },
    { label: "Fee Approvals",       count: stats.fees,                 to: "/admin/fees",         color: "danger" },
    { label: "APR Reviews (PhD)",   count: stats.aprs,                 to: "/admin/apr",         color: "secondary" },
  ];

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1">Admin Dashboard</h4>
      <p className="text-muted">Pending approvals and system overview</p>

      <h6 className="text-uppercase text-muted small fw-bold mb-2">System Overview</h6>
      <div className="row g-3 mb-4">
        {overviewCards.map(({ label, count, color }) => (
          <div key={label} className="col-6 col-lg-3">
            <div className={`card border-0 shadow-sm border-start border-4 border-${color} h-100`}>
              <div className="card-body">
                <p className="text-muted small mb-1">{label}</p>
                <span className={`fs-3 fw-bold text-${color}`}>{count}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <h6 className="text-uppercase text-muted small fw-bold mb-2">Pending Approvals</h6>
      <div className="row g-3 mb-4">
        {approvalCards.map(({ label, count, to, color }) => (
          <div key={label} className="col-6 col-md-4 col-lg-2">
            <Link to={to} className="text-decoration-none">
              <div className={`card border-0 shadow-sm border-start border-4 border-${color} h-100`}>
                <div className="card-body">
                  <p className="text-muted small mb-1">{label}</p>
                  <span className={`fs-3 fw-bold text-${color}`}>{count}</span>
                </div>
              </div>
            </Link>
          </div>
        ))}
      </div>
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-bold">Quick Actions</div>
        <div className="card-body d-flex flex-wrap gap-2">
          <Link to="/admin/student-review" className="btn btn-outline-warning btn-sm">Review Students</Link>
          <Link to="/admin/results"  className="btn btn-outline-primary btn-sm">Approve Results</Link>
          <Link to="/admin/fees"     className="btn btn-outline-danger btn-sm">Approve Fees</Link>
          <Link to="/admin/apr"      className="btn btn-outline-secondary btn-sm">Review APRs</Link>
          <Link to="/admin/courses"  className="btn btn-outline-info btn-sm">Manage Courses</Link>
          <Link to="/admin/academic" className="btn btn-outline-primary btn-sm">Manage Sessions & Programmes</Link>
          <Link to="/admin/timetable" className="btn btn-outline-info btn-sm">Manage Timetable</Link>
          <Link to="/admin/enrollments" className="btn btn-outline-warning btn-sm">Pending Enrollments</Link>
        </div>
      </div>
    </div>
  );
}
