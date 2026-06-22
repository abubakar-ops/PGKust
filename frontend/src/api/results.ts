import api from "./client";
import type { Result, SemesterResultBatch, GPAResponse } from "../types";

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
