import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../../api/client";

const useCount = (key: string, url: string) =>
  useQuery({
    queryKey: ["admin-dashboard", key],
    queryFn: async () => (await api.get<unknown[]>(url)).data.length,
  });

export default function AdminDashboard() {
  const totalStudents = useCount("totalStudents", "/accounts/admin/students/?status=ACTIVE");
  const totalLecturers = useCount("totalLecturers", "/accounts/admin/lecturers/?status=ACTIVE");
  const pendingStudents = useCount("pendingStudents", "/accounts/admin/students/pending/");
  const pendingLecturers = useCount("pendingLecturers", "/accounts/admin/lecturers/pending/");
  const batches = useCount("batches", "/results/batches/?status=PENDING");
  const fees = useCount("fees", "/fees/admin/list/?status=PENDING");
  const aprs = useCount("aprs", "/reports/apr/?status=SUBMITTED");

  const cards = [
    { label: "Total Students", query: totalStudents, subtitle: "Active students", to: "/admin/students/all", color: "success" },
    { label: "Total Lecturers", query: totalLecturers, subtitle: "Active lecturers", to: "/admin/lecturers/all", color: "primary" },
    { label: "Pending Students", query: pendingStudents, subtitle: "Awaiting review", to: "/admin/students", color: "warning" },
    { label: "Pending Lecturers", query: pendingLecturers, subtitle: "Awaiting approval", to: "/admin/lecturers", color: "info" },
    { label: "Result Batches", query: batches, subtitle: "Pending approval", to: "/admin/results", color: "primary" },
    { label: "Fee Approvals", query: fees, subtitle: "Awaiting payment review", to: "/admin/fees", color: "danger" },
    { label: "APR Reviews", query: aprs, subtitle: "PhD submissions", to: "/admin/apr", color: "secondary" },
  ];

  return (
    <div  className="container dashboard-shell py-4 text-start">
      <div className="dashboard-header" >
        <h4 style={{ color: "#fff" }} className="fw-bold mb-1">Admin Dashboard</h4>
        <p style={{ color: "#fff" }}>Institution overview and pending approvals</p>
      </div>
       <div className="card border-10 shadow-sm quick-actions">
        <div className="card-header bg-white fw-bold">Quick Actions</div>
        <div className="card-body d-flex flex-wrap gap-2">
          <Link to="/admin/students" className="btn btn-outline-warning btn-sm">Review Students</Link>
          <Link to="/admin/results" className="btn btn-outline-primary btn-sm">Approve Results</Link>
          <Link to="/admin/courses" className="btn btn-outline-info btn-sm">Manage Courses</Link>
          <Link to="/admin/enrollments" className="btn btn-outline-warning btn-sm">Pending Enrollments</Link>
        </div>
      </div>

      <div className="row g-3 mb-4">
        {cards.map(({ label, query, subtitle, to, color }) => (
          <div key={label} className="col-md-4 col-lg-3">
            <Link to={to} className="text-decoration-none">
              <div className={`card border-0 shadow-sm border-start border-4 border-${color} h-100 stat-card`}>
                <div className="card-body">
                  <p>{label}</p>
                  {query.isPending ? (
                    <div className="spinner-border spinner-border-sm text-secondary" role="status" aria-label="Loading" />
                  ) : query.isError ? (
                    <span className="fs-2 fw-bold text-muted">—</span>
                  ) : (
                    <span className={`fs-2 fw-bold text-${color}`}>{query.data}</span>
                  )}
                  <div className="small mt-1 text-secondary">{subtitle}</div>
                </div>
              </div>
            </Link>
          </div>
        ))}
      </div>

     
    </div>
  );
}
