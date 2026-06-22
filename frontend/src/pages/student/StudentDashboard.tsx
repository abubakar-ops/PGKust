import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { getGPA } from "../../api/results";
import { getFeeStatus } from "../../api/fees";
import { getMyEnrollments } from "../../api/courses";
import LoadingSpinner from "../../components/LoadingSpinner";
import type { GPAResponse, FeePayment, Enrollment, StudentProfile } from "../../types";

function CGPABadge({ cgpa }: { cgpa: string | undefined }) {
  if (!cgpa) return <span className="text-muted">—</span>;
  const val = parseFloat(cgpa);
  const cls = val >= 4.5 ? "success" : val >= 3.5 ? "info" : val >= 2.5 ? "warning" : "danger";
  const label = val >= 4.5 ? "Distinction" : val >= 3.5 ? "Merit" : val >= 2.5 ? "Pass" : "Fail";
  return (
    <span className={`badge bg-${cls} fs-6`}>
      {val.toFixed(2)} — {label}
    </span>
  );
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const [gpa, setGpa] = useState<GPAResponse | null>(null);
  const [fee, setFee] = useState<Partial<FeePayment> & { status?: string } | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([
      getGPA().then(({ data }) => setGpa(data)).catch(() => { /* no GPA yet */ }),
      getFeeStatus().then(({ data }) => setFee(data as Partial<FeePayment> & { status?: string })).catch(() => { /* no fee record */ }),
      getMyEnrollments().then(({ data }) => setEnrollments(data)).catch(() => { /* none */ }),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const profile = user?.profile as StudentProfile | null;
  const feeCleared = fee?.status === "APPROVED";
  const approvedCount = enrollments.filter((e) => e.status === "APPROVED").length;

  return (
    <div className="container py-4">
      <h4 className="fw-bold mb-1">Welcome, {user?.first_name}</h4>
      <p className="text-muted">{profile?.matric_number} · {profile?.programme}</p>

      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <h6 className="text-muted">CGPA</h6>
              <CGPABadge cgpa={gpa?.cumulative?.cgpa} />
              <div className="mt-2">
                <Link to="/student/gpa" className="btn btn-sm btn-outline-primary">View GPA →</Link>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <h6 className="text-muted">Annual Fee</h6>
              <span className={`badge bg-${feeCleared ? "success" : "danger"}`}>
                {feeCleared ? "Cleared" : (fee?.status ?? "Not Paid")}
              </span>
              <div className="mt-2">
                <Link to="/student/fees" className="btn btn-sm btn-outline-primary">Manage →</Link>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <h6 className="text-muted">Enrolled Courses</h6>
              <span className="fs-3 fw-bold text-primary">{approvedCount}</span>
              <div className="mt-2">
                <Link to="/student/courses" className="btn btn-sm btn-outline-primary">My Courses →</Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white fw-bold">Quick Links</div>
        <div className="card-body d-flex flex-wrap gap-2">
          <Link to="/student/timetable" className="btn btn-outline-secondary btn-sm">Timetable</Link>
          <Link to="/student/results" className="btn btn-outline-secondary btn-sm">Results</Link>
          {profile?.programme === "PHD" && (
            <Link to="/student/apr" className="btn btn-outline-secondary btn-sm">Annual Progress Report</Link>
          )}
          <Link to="/student/courses" className="btn btn-outline-secondary btn-sm">Enroll in Courses</Link>
        </div>
      </div>
    </div>
  );
}
