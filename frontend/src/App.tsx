import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/auth/LoginPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import ResetPasswordPage from "./pages/auth/ResetPasswordPage";
import ProfilePage from "./pages/ProfilePage";
import StudentRegisterPage from "./pages/auth/StudentRegisterPage";
import LecturerRegisterPage from "./pages/auth/LecturerRegisterPage";
import StudentDashboard from "./pages/student/StudentDashboard";
import LecturerDashboard from "./pages/lecturer/LecturerDashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminStudentsPage from "./pages/admin/AdminStudentsPage";
import AdminLecturersPage from "./pages/admin/AdminLecturersPage";
import AdminAllStudentsPage from "./pages/admin/AdminAllStudentsPage";
import AdminAllLecturersPage from "./pages/admin/AdminAllLecturersPage";
import AdminCourseAllocationPage from "./pages/admin/AdminCourseAllocationPage";
import AdminEnrollmentsPage from "./pages/admin/AdminEnrollmentsPage";
import AdminResultsPage from "./pages/admin/AdminResultsPage";
import NotificationsPage from "./pages/NotificationsPage";
import LecturerMaterialsPage from "./pages/lecturer/LecturerMaterialsPage";
import StudentCoursesPage from "./pages/student/StudentCoursesPage";
import StudentEnrollPage from "./pages/student/StudentEnrollPage";
import LecturerResultsUploadPage from "./pages/lecturer/LecturerResultsUploadPage";
import StudentResultsPage from "./pages/student/StudentResultsPage";
import LecturerAllocationsPage from "./pages/lecturer/LecturerAllocationsPage";
import StudentTimetablePage from "./pages/student/StudentTimetablePage";
import StudentMaterialsPage from "./pages/student/StudentMaterialsPage";
import StudentCourseMaterialsPage from "./pages/student/StudentCourseMaterialsPage";
import StudentFeesPage from "./pages/student/StudentFeesPage";
import LecturerTimetablePage from "./pages/lecturer/LecturerTimetablePage";
import AdminTimetablePage from "./pages/admin/AdminTimetablePage";
import AdminAcademicPage from "./pages/admin/AdminAcademicPage";
import AdminStudentReviewPage from "./pages/admin/AdminStudentReviewPage";

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
          <Route path="/forgot-password"     element={<ForgotPasswordPage />} />
          <Route path="/reset-password/:uid/:token" element={<ResetPasswordPage />} />
          <Route path="/register/student"    element={<StudentRegisterPage />} />
          <Route path="/register/lecturer"   element={<LecturerRegisterPage />} />
          <Route path="/unauthorized"        element={<div className="text-center p-5"><h3>403 — Access Denied</h3></div>} />

          {/* All authenticated users */}
          <Route element={<ProtectedRoute />}>
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>

          {/* Student */}
          <Route element={<ProtectedRoute allowedRoles={["STUDENT"]} />}>
            <Route path="/student/dashboard" element={<StudentDashboard />} />
            <Route path="/student/courses" element={<StudentCoursesPage />} />
            <Route path="/student/enroll" element={<StudentEnrollPage />} />
            <Route path="/student/results" element={<StudentResultsPage />} />
            <Route path="/student/gpa" element={<StudentResultsPage />} />
            <Route path="/student/timetable" element={<StudentTimetablePage />} />
            <Route path="/student/materials" element={<StudentMaterialsPage />} />
            <Route path="/student/materials/:allocationId" element={<StudentCourseMaterialsPage />} />
            <Route path="/student/fees" element={<StudentFeesPage />} />
          </Route>

          {/* Lecturer */}
          <Route element={<ProtectedRoute allowedRoles={["LECTURER"]} />}>
            <Route path="/lecturer/dashboard" element={<LecturerDashboard />} />
            <Route path="/lecturer/allocations" element={<LecturerAllocationsPage />} />
            <Route path="/lecturer/materials/:allocationId" element={<LecturerMaterialsPage />} />
            <Route path="/lecturer/results/upload" element={<LecturerResultsUploadPage />} />
            <Route path="/lecturer/timetable" element={<LecturerTimetablePage />} />
          </Route>

          {/* Admin */}
          <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/students" element={<AdminStudentsPage />} />
            <Route path="/admin/student-review" element={<AdminStudentReviewPage />} />
            <Route path="/admin/students/all" element={<AdminAllStudentsPage />} />
            <Route path="/admin/lecturers" element={<AdminLecturersPage />} />
            <Route path="/admin/lecturers/all" element={<AdminAllLecturersPage />} />
            <Route path="/admin/courses" element={<AdminCourseAllocationPage />} />
            <Route path="/admin/academic" element={<AdminAcademicPage />} />
            <Route path="/admin/enrollments" element={<AdminEnrollmentsPage />} />
            <Route path="/admin/results" element={<AdminResultsPage />} />
            <Route path="/admin/timetable" element={<AdminTimetablePage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
