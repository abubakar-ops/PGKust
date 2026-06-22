import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getNotifications } from "../api/notifications";
import type { StudentProfile } from "../types";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!user) return;
    getNotifications()
      .then(({ data }) => setUnread(data.count))
      .catch(() => { /* ignore */ });
  }, [user]);

  const handleLogout = async () => { await logout(); navigate("/login"); };

  if (!user) return null;

  const studentProfile = user.role === "STUDENT" ? (user.profile as StudentProfile | null) : null;

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container">
        <Link className="navbar-brand fw-bold" to="/">KUST CS PGMS</Link>
        <button className="navbar-toggler" type="button"
          data-bs-toggle="collapse" data-bs-target="#navMain"
          aria-controls="navMain" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon" />
        </button>
        <div className="collapse navbar-collapse" id="navMain">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            {user.role === "STUDENT" && <>
              <li className="nav-item"><Link className="nav-link" to="/student/dashboard">Dashboard</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/student/courses">Courses</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/student/timetable">Timetable</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/student/results">Results</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/student/gpa">GPA</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/student/fees">Fees</Link></li>
              {studentProfile?.programme === "PHD" && (
                <li className="nav-item"><Link className="nav-link" to="/student/apr">APR</Link></li>
              )}
            </>}
            {user.role === "LECTURER" && <>
              <li className="nav-item"><Link className="nav-link" to="/lecturer/dashboard">Dashboard</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/lecturer/allocations">My Courses</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/lecturer/timetable">Timetable</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/lecturer/results/upload">Upload Results</Link></li>
            </>}
            {user.role === "ADMIN" && <>
              <li className="nav-item"><Link className="nav-link" to="/admin/dashboard">Dashboard</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/admin/students">Students</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/admin/lecturers">Lecturers</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/admin/courses">Courses</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/admin/results">Results</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/admin/fees">Fees</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/admin/apr">APRs</Link></li>
            </>}
          </ul>
          <div className="d-flex align-items-center gap-3">
            <Link to="/notifications" className="text-white position-relative" aria-label="Notifications">
              <i className="bi bi-bell-fill fs-5" />
              {unread > 0 && (
                <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                  {unread}
                </span>
              )}
            </Link>
            <span className="text-white small">{user.first_name} {user.last_name}</span>
            <button className="btn btn-outline-light btn-sm" onClick={() => void handleLogout()}>
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
