import api from "./client";
import type { NotificationListResponse } from "../types";

export const getNotifications = () =>
  api.get<NotificationListResponse>("/notifications/");
export const markRead = (pk: number) =>
  api.post(`/notifications/${pk}/read/`);
export const markAllRead = () =>
  api.post("/notifications/read-all/");
