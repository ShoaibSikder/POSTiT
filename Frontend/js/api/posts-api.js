import { API_PATHS } from "../config.js";
import { request, withQuery } from "./api-client.js";

export const getFeed = (page = 1) =>
  request(withQuery(API_PATHS.feed, { page }));

export const getPosts = (params = {}) =>
  request(withQuery(API_PATHS.posts, params));

export const getUserPosts = (username, page = 1) =>
  request(withQuery(`/users/${encodeURIComponent(username)}/posts/`, { page }));

export const createPost = ({ content, images = [] }) => {
  const body = new FormData();
  body.set("content", content || "");
  images.forEach((image) => body.append("images", image));
  return request(API_PATHS.posts, { method: "POST", body });
};

export const updatePost = (postId, content) =>
  request(`${API_PATHS.posts}${postId}/`, {
    method: "PATCH",
    body: { content },
  });

export const deletePost = (postId) =>
  request(`${API_PATHS.posts}${postId}/`, { method: "DELETE" });

export const likePost = (postId) =>
  request(`/posts/${postId}/like/`, { method: "POST", body: {} });

export const unlikePost = (postId) =>
  request(`/posts/${postId}/like/`, { method: "DELETE", body: {} });