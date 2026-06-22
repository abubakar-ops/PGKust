import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/auth/LoginPage";
import StudentRegisterPage from "./pages/auth/StudentRegisterPage";
import LecturerRegisterPage from "./pages/auth/LecturerRegisterPage";
import StudentDashboard from "./pages/student/StudentDashboard";
import LecturerDashboard from "./pages/lecturer/LecturerDashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import NotificationsPage from "./pages/NotificationsPage";

function RoleRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "STUDENT")  return <Navigate to="/student/dashboard" replace />;
  if (user.role === "LECTURER") return <Navigate to="/lecturer/dashboard" replace />;
  return <Navigate to="/admin/dashboard" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          {/* Public */}
          <Route path="/"                    element={<RoleRedirect />} />
          <Route path="/login"               element={<LoginPage />} />
          <Route path="/register/student"    element={<StudentRegisterPage />} />
          <Route path="/register/lecturer"   element={<LecturerRegisterPage />} />
          <Route path="/unauthorized"        element={<div className="text-center p-5"><h3>403 — Access Denied</h3></div>} />

          {/* All authenticated users */}
          <Route element={<ProtectedRoute />}>
            <Route path="/notifications" element={<NotificationsPage />} />
          </Route>

          {/* Student */}
          <Route element={<ProtectedRoute allowedRoles={["STUDENT"]} />}>
            <Route path="/student/dashboard" element={<StudentDashboard />} />
          </Route>

          {/* Lecturer */}
          <Route element={<ProtectedRoute allowedRoles={["LECTURER"]} />}>
            <Route path="/lecturer/dashboard" element={<LecturerDashboard />} />
          </Route>

          {/* Admin */}
          <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
