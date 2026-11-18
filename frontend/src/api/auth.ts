import api from "./client";
import type { AuthUser, StudentProfile, StudentReview, LecturerProfile } from "../types";

export interface LoginResponse { access: string; refresh: string; }

export const login = (email: string, password: string) =>
  api.post<LoginResponse>("/auth/login/", { email, password });

export const logout = (refresh: string) =>
  api.post("/auth/logout/", { refresh });

export const getMe = () =>
  api.get<AuthUser>("/accounts/me/");

export const updateMyProfile = (data: FormData) =>
  api.patch<AuthUser>("/accounts/me/", data, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const changePassword = (data: {
  current_password: string;
  new_password: string;
  confirm_password: string;
}) => api.post<{ detail: string }>("/accounts/change-password/", data);

export const requestPasswordReset = (email: string) =>
  api.post<{ detail: string }>("/accounts/forgot-password/", { email });

export const resetPassword = (
  uid: string,
  token: string,
  data: { new_password: string; confirm_password: string },
) => api.post<{ detail: string }>(`/accounts/reset-password/${uid}/${token}/`, data);

export interface AdminDashboardStats {
  total_students: number;
  total_lecturers: number;
  total_courses: number;
  total_enrollments: number;
  pending_enrollments: number;
}

export const getAdminDashboardStats = () =>
  api.get<AdminDashboardStats>("/accounts/admin/dashboard-stats/");

export const registerStudent = (data: Record<string, unknown>) =>
  api.post<{ success: boolean; detail: string }>("/accounts/register/student/", data);

export const registerLecturer = (data: Record<string, unknown>) =>
  api.post<{ success: boolean; detail: string }>("/accounts/register/lecturer/", data);

export const getPendingStudents = () =>
  api.get<StudentProfile[]>("/accounts/admin/students/pending/");

export const getAllStudents = (statusFilter?: string, search?: string) =>
  api.get<StudentProfile[]>("/accounts/admin/students/", {
    params: {
      ...(statusFilter ? { status: statusFilter } : {}),
      ...(search ? { search } : {}),
    },
  });

export const getAdminStudentReview = (pk: number) =>
  api.get<StudentReview>(`/accounts/admin/students/${pk}/review/`);

export const updateStudent = (pk: number, data: {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  matric_number?: string;
  programme?: StudentProfile["programme"];
  admission_year?: number;
}) =>
  api.patch<StudentProfile>(`/accounts/admin/students/${pk}/`, data);

export const approveStudent = (pk: number, action: "approve" | "reject") =>
  api.post(`/accounts/admin/students/${pk}/approve/`, { action });

export const getPendingLecturers = () =>
  api.get<LecturerProfile[]>("/accounts/admin/lecturers/pending/");

export const getAllLecturers = (statusFilter?: string, search?: string) =>
  api.get<LecturerProfile[]>("/accounts/admin/lecturers/", {
    params: {
      ...(statusFilter ? { status: statusFilter } : {}),
      ...(search ? { search } : {}),
    },
  });

export const updateLecturer = (pk: number, data: {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  staff_id?: string;
  specialization?: string;
  is_supervisor?: boolean;
}) =>
  api.patch<LecturerProfile>(`/accounts/admin/lecturers/${pk}/`, data);

export const approveLecturer = (pk: number, action: "approve" | "reject") =>
  api.post(`/accounts/admin/lecturers/${pk}/approve/`, { action });
