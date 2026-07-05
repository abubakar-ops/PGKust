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
import AdminStudentsPage from "./pages/admin/AdminStudentsPage";
import AdminLecturersPage from "./pages/admin/AdminLecturersPage";
import NotificationsPage from "./pages/NotificationsPage";
import LecturerMaterialsPage from "./pages/lecturer/LecturerMaterialsPage";
import StudentCoursesPage from "./pages/student/StudentCoursesPage";
import LecturerResultsUploadPage from "./pages/lecturer/LecturerResultsUploadPage";
import StudentResultsPage from "./pages/student/StudentResultsPage";
import LecturerAllocationsPage from "./pages/lecturer/LecturerAllocationsPage";

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
            <Route path="/student/courses" element={<StudentCoursesPage />} />
            <Route path="/student/results" element={<StudentResultsPage />} />
            <Route path="/student/gpa" element={<StudentResultsPage />} />
          </Route>

          {/* Lecturer */}
          <Route element={<ProtectedRoute allowedRoles={["LECTURER"]} />}>
            <Route path="/lecturer/dashboard" element={<LecturerDashboard />} />
            <Route path="/lecturer/allocations" element={<LecturerAllocationsPage />} />
            <Route path="/lecturer/materials/:allocationId" element={<LecturerMaterialsPage />} />
            <Route path="/lecturer/results/upload" element={<LecturerResultsUploadPage />} />
          </Route>

          {/* Admin */}
          <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/students" element={<AdminStudentsPage />} />
            <Route path="/admin/lecturers" element={<AdminLecturersPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
