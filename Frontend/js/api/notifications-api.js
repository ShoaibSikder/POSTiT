import { API_PATHS } from "../config.js";
import { request, withQuery } from "./api-client.js";

export const getNotifications = (page = 1) =>
  request(withQuery(API_PATHS.notifications, { page }));

export const markNotificationRead = (notificationId) =>
  request(`/notifications/${notificationId}/read/`, {
    method: "POST",
    body: {},
  });

export const markAllNotificationsRead = () =>
  request("/notifications/read-all/", { method: "POST", body: {} });