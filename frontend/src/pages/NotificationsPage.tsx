import { useState, useEffect, useCallback } from "react";
import { getNotifications, markRead, markAllRead } from "../api/notifications";
import LoadingSpinner from "../components/LoadingSpinner";
import type { Notification } from "../types";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    void getNotifications()
      .then(({ data }) => setNotifications(data.results))
      .catch(() => { /* ignore */ })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleMarkRead = (pk: number) => void markRead(pk).then(load);
  const handleMarkAll  = () => void markAllRead().then(load);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="fw-bold mb-0">Notifications</h5>
        <button className="btn btn-sm btn-outline-secondary" onClick={handleMarkAll}>
          Mark All Read
        </button>
      </div>
      {notifications.length === 0 && (
        <div className="text-center text-muted py-5">No notifications.</div>
      )}
      <div className="list-group">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`list-group-item list-group-item-action d-flex justify-content-between align-items-start ${!n.is_read ? "list-group-item-light fw-semibold" : ""}`}
          >
            <div>
              <small className="text-muted">[{n.notification_type}]</small>
              <div>{n.title}</div>
              <small className="text-muted">{n.message}</small>
              <div><small className="text-muted">{new Date(n.created_at).toLocaleString()}</small></div>
            </div>
            {!n.is_read && (
              <button
                className="btn btn-sm btn-outline-primary ms-3 flex-shrink-0"
                onClick={() => handleMarkRead(n.id)}
              >
                Mark read
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
