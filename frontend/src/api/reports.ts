import api from "./client";
import type { AnnualProgressReport } from "../types";

export const getAPRs = (params?: Record<string, string>) =>
  api.get<AnnualProgressReport[]>("/reports/apr/", { params });
export const createAPR = (data: Record<string, unknown>) =>
  api.post<AnnualProgressReport>("/reports/apr/create/", data);
export const getAPR = (pk: number) =>
  api.get<AnnualProgressReport>(`/reports/apr/${pk}/`);
export const updateAPR = (pk: number, data: Partial<AnnualProgressReport>) =>
  api.patch<AnnualProgressReport>(`/reports/apr/${pk}/`, data);
export const submitAPR = (pk: number) =>
  api.post(`/reports/apr/${pk}/submit/`);
export const endorseAPR = (pk: number, comments: string) =>
  api.post(`/reports/apr/${pk}/endorse/`, { comments });
export const approveAPR = (pk: number, action: "approve" | "reject", comments?: string) =>
  api.post(`/reports/apr/${pk}/approve/`, { action, comments });
export const downloadTranscript = () =>
  api.get("/reports/transcript/", { responseType: "blob" });
