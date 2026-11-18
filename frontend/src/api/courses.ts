import api from "./client";
import type {
  AcademicSession, Course, CourseAllocation, TimetableEntry,
  Enrollment, CourseMaterial, AvailableAllocation, Programme,
} from "../types";

export const getCurrentSession = () => api.get<AcademicSession>("/courses/session/current/");
export const getCourses = (params?: Record<string, string>) =>
  api.get<Course[]>("/courses/list/", { params });
export const getTimetable = () => api.get<TimetableEntry[]>("/courses/timetable/");
export const enroll = (allocation: number) =>
  api.post<Enrollment>("/courses/enroll/", { allocation });
export const getMyEnrollments = () => api.get<Enrollment[]>("/courses/enrollments/");
export const getAvailableAllocations = () =>
  api.get<AvailableAllocation[]>("/courses/available/");
export const getMyAllocations = () => api.get<CourseAllocation[]>("/courses/allocations/");
export const getMaterials = (allocationPk: number) =>
  api.get<CourseMaterial[]>(`/courses/materials/${allocationPk}/`);
export const getRecentMaterials = (limit = 5) =>
  api.get<CourseMaterial[]>("/courses/materials/recent/", { params: { limit } });
export const uploadMaterial = (allocationPk: number, formData: FormData) =>
  api.post<CourseMaterial>(`/courses/materials/${allocationPk}/upload/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const deleteMaterial = (allocationPk: number, materialPk: number) =>
  api.delete(`/courses/materials/${allocationPk}/${materialPk}/`);

// Admin
export const adminAllocateCourse = (data: Record<string, unknown>) =>
  api.post<CourseAllocation>("/courses/admin/allocate/", data);
export const adminGetSessions = () =>
  api.get<AcademicSession[]>("/courses/admin/sessions/");
export const adminCreateSession = (data: Omit<AcademicSession, "id">) =>
  api.post<AcademicSession>("/courses/admin/sessions/", data);
export const adminUpdateSession = (pk: number, data: Partial<Omit<AcademicSession, "id">>) =>
  api.patch<AcademicSession>(`/courses/admin/sessions/${pk}/`, data);
export const adminDeleteSession = (pk: number) =>
  api.delete(`/courses/admin/sessions/${pk}/`);
export const adminGetProgrammes = () =>
  api.get<Programme[]>("/courses/admin/programmes/");
export const adminCreateProgramme = (data: Omit<Programme, "id">) =>
  api.post<Programme>("/courses/admin/programmes/", data);
export const adminUpdateProgramme = (pk: number, data: Partial<Omit<Programme, "id">>) =>
  api.patch<Programme>(`/courses/admin/programmes/${pk}/`, data);
export const adminDeleteProgramme = (pk: number) =>
  api.delete(`/courses/admin/programmes/${pk}/`);
export const adminGetCourses = () =>
  api.get<Course[]>("/courses/admin/courses/");
export const adminCreateCourse = (data: Omit<Course, "id" | "programme_name">) =>
  api.post<Course>("/courses/admin/courses/", data);
export const adminUpdateCourse = (pk: number, data: Partial<Omit<Course, "id" | "programme_name">>) =>
  api.patch<Course>(`/courses/admin/courses/${pk}/`, data);
export const adminDeleteCourse = (pk: number) =>
  api.delete(`/courses/admin/courses/${pk}/`);
export const adminGetAllocations = () =>
  api.get<CourseAllocation[]>("/courses/admin/allocations/");
export const adminCreateTimetable = (data: Record<string, unknown>) =>
  api.post<TimetableEntry>("/courses/admin/timetable/", data);
export const adminGetTimetable = () =>
  api.get<TimetableEntry[]>("/courses/admin/timetable/");
export const adminUpdateTimetable = (pk: number, data: Record<string, unknown>) =>
  api.patch<TimetableEntry>(`/courses/admin/timetable/${pk}/`, data);
export const adminDeleteTimetable = (pk: number) =>
  api.delete(`/courses/admin/timetable/${pk}/`);
export const adminPendingEnrollments = () =>
  api.get<Enrollment[]>("/courses/admin/enrollments/pending/");
export const adminApproveEnrollment = (pk: number, action: "approve" | "reject") =>
  api.post(`/courses/admin/enrollments/${pk}/approve/`, { action });
