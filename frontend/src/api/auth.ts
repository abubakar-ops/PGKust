import api from "./client";
import type { AuthUser, StudentProfile, LecturerProfile } from "../types";

export interface LoginResponse { access: string; refresh: string; }

export const login = (email: string, password: string) =>
  api.post<LoginResponse>("/auth/login/", { email, password });

export const logout = (refresh: string) =>
  api.post("/auth/logout/", { refresh });

export const getMe = () =>
  api.get<AuthUser>("/accounts/me/");

export const registerStudent = (data: Record<string, unknown>) =>
  api.post<{ success: boolean; detail: string }>("/accounts/register/student/", data);

export const registerLecturer = (data: Record<string, unknown>) =>
  api.post<{ success: boolean; detail: string }>("/accounts/register/lecturer/", data);

export const getPendingStudents = () =>
  api.get<StudentProfile[]>("/accounts/admin/students/pending/");

export const getAllStudents = (statusFilter?: string) =>
  api.get<StudentProfile[]>("/accounts/admin/students/", {
    params: statusFilter ? { status: statusFilter } : {},
  });

export const updateStudent = (
  pk: number,
  data: Partial<Pick<StudentProfile, "first_name" | "last_name" | "matric_number" | "programme" | "admission_year" | "supervisor">>,
) =>
  api.patch<StudentProfile>(`/accounts/admin/students/${pk}/`, data);

export const getSupervisedStudents = () =>
  api.get<StudentProfile[]>("/accounts/lecturer/students/");

export const approveStudent = (pk: number, action: "approve" | "reject") =>
  api.post(`/accounts/admin/students/${pk}/approve/`, { action });

export const changeStudentStatus = (pk: number, action: "reactivate" | "graduate" | "suspend") =>
  api.post<StudentProfile>(`/accounts/admin/students/${pk}/status/`, { action });

export const getPendingLecturers = () =>
  api.get<LecturerProfile[]>("/accounts/admin/lecturers/pending/");

export const getAllLecturers = (statusFilter?: string) =>
  api.get<LecturerProfile[]>("/accounts/admin/lecturers/", {
    params: statusFilter ? { status: statusFilter } : {},
  });

export const updateLecturer = (
  pk: number,
  data: Partial<Pick<LecturerProfile, "first_name" | "last_name" | "staff_id" | "specialization" | "is_supervisor">>,
) =>
  api.patch<LecturerProfile>(`/accounts/admin/lecturers/${pk}/`, data);

export const approveLecturer = (pk: number, action: "approve" | "reject") =>
  api.post(`/accounts/admin/lecturers/${pk}/approve/`, { action });
