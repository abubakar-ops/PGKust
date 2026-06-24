import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getNotifications, markRead, markAllRead } from "../api/notifications";
import type { StudentProfile, Notification } from "../types";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadNotifications = () => {
    if (!user) return;
    void getNotifications()
      .then(({ data }) => {
        setUnread(data.count);
        setNotifications(data.results);
      })
      .catch(() => { /* ignore */ });
  };

  useEffect(loadNotifications, [user]);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const handleLogout = async () => { await logout(); navigate("/login"); };

  const handleOpenNotification = (n: Notification) => {
    if (!n.is_read) void markRead(n.id).then(loadNotifications);
    setShowDropdown(false);
    if (n.link) navigate(n.link);
  };

  const handleMarkAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    void markAllRead().then(loadNotifications);
  };

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
            <div className="position-relative" ref={dropdownRef}>
              <button
                type="button"
                className="btn btn-link text-white position-relative p-0 border-0"
                aria-label="Notifications"
                onClick={() => setShowDropdown((v) => !v)}
              >
                <i className="bi bi-bell-fill fs-5" />
                {unread > 0 && (
                  <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                    {unread}
                  </span>
                )}
              </button>
              {showDropdown && (
                <div
                  className="dropdown-menu show p-0"
                  style={{ right: 0, left: "auto", width: 340, maxHeight: 420, overflowY: "auto" }}
                >
                  <div className="d-flex justify-content-between align-items-center px-3 py-2 border-bottom">
                    <span className="fw-bold small">Notifications</span>
                    <button className="btn btn-sm btn-link p-0" onClick={handleMarkAll}>
                      Mark all read
                    </button>
                  </div>
                  {notifications.length === 0 ? (
                    <div className="text-center text-muted small py-4">No notifications.</div>
                  ) : (
                    notifications.slice(0, 10).map((n) => (
                      <button
                        key={n.id}
                        type="button"
                        className={`dropdown-item py-2 border-bottom ${!n.is_read ? "fw-semibold" : ""}`}
                        onClick={() => handleOpenNotification(n)}
                      >
                        <div className="small text-muted">[{n.notification_type}]</div>
                        <div>{n.title}</div>
                        <div className="small text-muted text-truncate">{n.message}</div>
                        <div className="small text-muted">{new Date(n.created_at).toLocaleString()}</div>
                      </button>
                    ))
                  )}
                  <Link
                    to="/notifications"
                    className="d-block text-center small py-2 border-top"
                    onClick={() => setShowDropdown(false)}
                  >
                    View all
                  </Link>
                </div>
              )}
            </div>
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
