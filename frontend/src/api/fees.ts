import api from "./client";
import type { FeePayment } from "../types";

export const getFeeStatus = () => api.get<FeePayment | { academic_year: string; status: string }>("/fees/status/");
export const payManual = (formData: FormData) =>
  api.post<FeePayment>("/fees/pay/manual/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const initOnlinePayment = (amount: number) =>
  api.post<{ authorization_url: string; reference: string }>("/fees/pay/online/initialize/", { amount });
export const adminFeeList = (params?: Record<string, string>) =>
  api.get<FeePayment[]>("/fees/admin/list/", { params });
export const adminApproveFee = (pk: number, action: "approve" | "reject", reason?: string) =>
  api.post(`/fees/admin/${pk}/approve/`, { action, reason });
