import api from "./client";
import type {
  AcademicSession, Course, CourseAllocation, TimetableEntry,
  Enrollment, CourseMaterial,
} from "../types";

export const getCurrentSession = () => api.get<AcademicSession>("/courses/session/current/");
export const getCourses = (params?: Record<string, string>) =>
  api.get<Course[]>("/courses/list/", { params });
export const getTimetable = () => api.get<TimetableEntry[]>("/courses/timetable/");
export const enroll = (allocation: number) =>
  api.post<Enrollment>("/courses/enroll/", { allocation });
export const getMyEnrollments = () => api.get<Enrollment[]>("/courses/enrollments/");
export const getMyAllocations = () => api.get<CourseAllocation[]>("/courses/allocations/");
export const getMaterials = (allocationPk: number) =>
  api.get<CourseMaterial[]>(`/courses/materials/${allocationPk}/`);
export const uploadMaterial = (allocationPk: number, formData: FormData) =>
  api.post<CourseMaterial>(`/courses/materials/${allocationPk}/upload/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// Admin
export const adminAllocateCourse = (data: Record<string, unknown>) =>
  api.post<CourseAllocation>("/courses/admin/allocate/", data);
export const adminCreateTimetable = (data: Record<string, unknown>) =>
  api.post<TimetableEntry>("/courses/admin/timetable/", data);
export const adminPendingEnrollments = () =>
  api.get<Enrollment[]>("/courses/admin/enrollments/pending/");
export const adminApproveEnrollment = (pk: number, action: "approve" | "reject") =>
  api.post(`/courses/admin/enrollments/${pk}/approve/`, { action });
