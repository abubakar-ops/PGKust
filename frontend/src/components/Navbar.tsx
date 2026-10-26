import { useState, useEffect, useRef } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getNotifications, markRead, markAllRead } from "../api/notifications";
import type { StudentProfile, Notification } from "../types";

export default function Navbar() {
  const { user, logout, loadUser } = useAuth();
  const navigate = useNavigate();
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
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
    void loadUser();
    if (n.link) navigate(n.link);
  };

  const handleMarkAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    void markAllRead().then(loadNotifications);
  };

  if (!user) return null;

  const studentProfile = user.role === "STUDENT" ? (user.profile as StudentProfile | null) : null;
  const initials = `${user.first_name?.[0] ?? ""}${user.last_name?.[0] ?? ""}`.toUpperCase();
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `nav-link${isActive ? " active" : ""}`;

  return (
    <>
      <div className="topbar-actions">
        <div className="position-relative" ref={dropdownRef}>
          <button
            type="button"
            className="btn btn-link text-white position-relative px-2 py-1 border-0 topbar-notification"
            aria-label="Notifications"
            onClick={() => setShowDropdown((v) => !v)}
          >
            <i className="bi bi-bell-fill fs-5" />
            <span className="ms-2 notification-label">Notifications</span>
            {unread > 0 && (
              <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                {unread}
              </span>
            )}
          </button>
          {showDropdown && (
            <div className="dropdown-menu show p-0 notification-panel">
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
      </div>

      <nav className={`navbar navbar-expand-lg navbar-dark app-sidebar ${sidebarOpen ? "is-open" : "is-collapsed"}`}>
        <div className="container d-flex flex-column px-3 h-100">
          <div className="d-flex align-items-center justify-content-between mb-2 gap-2 sidebar-header">
            <button
              type="button"
              className="sidebar-toggle d-none d-lg-inline-flex"
              aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              onClick={() => setSidebarOpen((value) => !value)}
            >
              <i className={`bi ${sidebarOpen ? "bi-chevron-double-left" : "bi-chevron-double-right"}`} />
            </button>
            {sidebarOpen && (
              <Link className="navbar-brand fw-bold d-flex align-items-center gap-2 py-2 mb-0 brand-text" to="/">
                <span className="brand-mark">CS</span>
                <span>ADUST CS PGMS</span>
              </Link>
            )}
            <button className="navbar-toggler" type="button"
              data-bs-toggle="collapse" data-bs-target="#navMain"
              aria-controls="navMain" aria-expanded="false" aria-label="Toggle navigation">
              <span className="navbar-toggler-icon" />
            </button>
          </div>
          <div className="collapse navbar-collapse sidebar-body" id="navMain">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              {user.role === "STUDENT" && <>
                <li className="nav-item"><NavLink className={navLinkClass} to="/student/dashboard"><i className="bi bi-speedometer2 nav-icon" /><span className="nav-label">Dashboard</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/student/courses"><i className="bi bi-journal-bookmark nav-icon" /><span className="nav-label">Courses</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/student/timetable"><i className="bi bi-calendar3 nav-icon" /><span className="nav-label">Timetable</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/student/results"><i className="bi bi-clipboard-data nav-icon" /><span className="nav-label">Results</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/student/fees"><i className="bi bi-cash-coin nav-icon" /><span className="nav-label">Fees</span></NavLink></li>
                {studentProfile?.programme === "PHD" && (
                  <li className="nav-item"><NavLink className={navLinkClass} to="/student/apr"><i className="bi bi-file-earmark-text nav-icon" /><span className="nav-label">APR</span></NavLink></li>
                )}
              </>}
              {user.role === "LECTURER" && <>
                <li className="nav-item"><NavLink className={navLinkClass} to="/lecturer/dashboard"><i className="bi bi-speedometer2 nav-icon" /><span className="nav-label">Dashboard</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/lecturer/allocations"><i className="bi bi-journal-bookmark nav-icon" /><span className="nav-label">My Courses</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/lecturer/timetable"><i className="bi bi-calendar3 nav-icon" /><span className="nav-label">Timetable</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/lecturer/results/upload"><i className="bi bi-cloud-upload nav-icon" /><span className="nav-label">Upload Results</span></NavLink></li>
              </>}
              {user.role === "ADMIN" && <>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/dashboard"><i className="bi bi-speedometer2 nav-icon" /><span className="nav-label">Dashboard</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/students"><i className="bi bi-people nav-icon" /><span className="nav-label">Students</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/lecturers"><i className="bi bi-person-workspace nav-icon" /><span className="nav-label">Lecturers</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/courses"><i className="bi bi-journal-bookmark nav-icon" /><span className="nav-label">Courses</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/results"><i className="bi bi-clipboard-data nav-icon" /><span className="nav-label">Results</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/fees"><i className="bi bi-cash-coin nav-icon" /><span className="nav-label">Fees</span></NavLink></li>
                <li className="nav-item"><NavLink className={navLinkClass} to="/admin/apr"><i className="bi bi-file-earmark-text nav-icon" /><span className="nav-label">APRs</span></NavLink></li>
              </>}
            </ul>
          </div>

          <div className="sidebar-footer mt-auto border-top border-light border-opacity-25 pt-3">
            <div className="sidebar-user">
              <span className="user-avatar">{initials || "?"}</span>
              <span className="text-white small user-name">{user.first_name} {user.last_name}</span>
            </div>
            <button className="btn btn-logout btn-sm w-100" onClick={() => void handleLogout()}>
              <i className="bi bi-box-arrow-right nav-icon" /> <span className="nav-label">Logout</span>
            </button>
          </div>
        </div>
      </nav>
    </>
  );
}
