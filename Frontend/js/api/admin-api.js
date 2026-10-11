import { request, withQuery } from "./api-client.js";

export const getAdminDashboard = () => request("/admin/dashboard/");
export const getAdminUsers = (params = {}) =>
  request(withQuery("/admin/users/", params));
export const moderateUser = (id, action, reason) =>
  request(`/admin/users/${id}/${action}/`, {
    method: "POST",
    body: { reason },
  });
export const getAdminPosts = (page = 1) =>
  request(withQuery("/admin/posts/", { page }));
export const deleteAdminPost = (id, reason) =>
  request(`/admin/posts/${id}/`, { method: "DELETE", body: { reason } });
export const getAdminComments = (page = 1) =>
  request(withQuery("/admin/comments/", { page }));
export const deleteAdminComment = (id, reason) =>
  request(`/admin/comments/${id}/`, { method: "DELETE", body: { reason } });
export const getAdminMedia = (type, page = 1) =>
  request(withQuery(`/admin/media/${type}/`, { page }));
export const deleteAdminMedia = (type, id, reason) =>
  request(`/admin/media/${type}/${id}/`, { method: "DELETE", body: { reason } });
export const getAdminNotifications = (params = {}) =>
  request(withQuery("/admin/notifications/", params));
export const deleteAdminNotification = (id, reason) =>
  request(`/admin/notifications/${id}/`, {
    method: "DELETE",
    body: { reason },
  });
export const getAdminRelationships = () => request("/admin/relationships/");
export const getAdminAudit = (params = {}) =>
  request(withQuery("/admin/audit/", params));
export const getAdminActivity = (params = {}) =>
  request(withQuery("/admin/activity/", params));
export const getAdminSettings = () => request("/admin/settings/");
export const updateAdminSetting = (key, value) =>
  request("/admin/settings/", { method: "PUT", body: { key, value } });
