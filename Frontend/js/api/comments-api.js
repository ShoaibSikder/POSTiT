import { request } from "./api-client.js";

export const getComments = (postId, page = 1) =>
  request(`/posts/${postId}/comments/?page=${page}`);

export const addComment = (postId, content) =>
  request(`/posts/${postId}/comments/`, {
    method: "POST",
    body: { content },
  });

export const updateComment = (commentId, content) =>
  request(`/comments/${commentId}/`, {
    method: "PATCH",
    body: { content },
  });

export const deleteComment = (commentId) =>
  request(`/comments/${commentId}/`, { method: "DELETE" });