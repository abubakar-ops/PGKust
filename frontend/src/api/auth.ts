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

export const updateStudent = (pk: number, data: Record<string, unknown>) =>
  api.patch<StudentProfile>(`/accounts/admin/students/${pk}/`, data);

export const approveStudent = (pk: number, action: "approve" | "reject") =>
  api.post(`/accounts/admin/students/${pk}/approve/`, { action });

export const getPendingLecturers = () =>
  api.get<LecturerProfile[]>("/accounts/admin/lecturers/pending/");

export const updateLecturer = (pk: number, data: Record<string, unknown>) =>
  api.patch<LecturerProfile>(`/accounts/admin/lecturers/${pk}/`, data);

export const approveLecturer = (pk: number, action: "approve" | "reject") =>
  api.post(`/accounts/admin/lecturers/${pk}/approve/`, { action });
