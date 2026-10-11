import { API_PATHS } from "../config.js";
import { request, withQuery } from "./api-client.js";

export const getMyProfile = () => request(API_PATHS.profile);

export const getUserProfile = (username) =>
  request(`/users/${encodeURIComponent(username)}/`);

export const updateProfile = (formData) =>
  request(API_PATHS.profile, { method: "PATCH", body: formData });

export const getUserMedia = (username, page = 1) =>
  request(withQuery(`/users/${encodeURIComponent(username)}/media/`, { page }));

export const addProfileMedia = (username, image, caption) => {
  const body = new FormData();
  body.set("image", image);
  body.set("caption", caption);
  return request(`/users/${encodeURIComponent(username)}/media/`, {
    method: "POST",
    body,
  });
};

export const deleteProfileMedia = (mediaId) =>
  request(`/profile-media/${mediaId}/`, { method: "DELETE" });