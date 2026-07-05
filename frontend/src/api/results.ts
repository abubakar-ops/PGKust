import api from "./client";
import type { Result, SemesterResultBatch, GPAResponse, ExcelUploadResponse } from "../types";

export const getMyResults = (params?: Record<string, string>) =>
  api.get<Result[]>("/results/mine/", { params });
export const getGPA = () => api.get<GPAResponse>("/results/gpa/");
export const uploadResults = (data: Record<string, unknown>) =>
  api.post("/results/upload/", data);
export const getBatches = (params?: Record<string, string>) =>
  api.get<SemesterResultBatch[]>("/results/batches/", { params });
export const createBatch = (data: Record<string, unknown>) =>
  api.post<SemesterResultBatch>("/results/batches/", data);
export const approveBatch = (pk: number, action: "approve" | "reject", comment?: string) =>
  api.post(`/results/batches/${pk}/approve/`, { action, comment });
export const downloadScoreSheetTemplate = (allocationPk: number) =>
  api.get<Blob>(`/results/template/${allocationPk}/`, { responseType: "blob" });
export const uploadResultsExcel = (allocationPk: number, formData: FormData) =>
  api.post<ExcelUploadResponse>(`/results/upload-excel/${allocationPk}/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
