import { request } from "./api-client.js";
import { withQuery } from "./api-client.js";

export const followUser = (username) =>
  request(`/users/${encodeURIComponent(username)}/follow/`, {
    method: "POST",
    body: {},
  });

export const unfollowUser = (username) =>
  request(`/users/${encodeURIComponent(username)}/follow/`, {
    method: "DELETE",
    body: {},
  });

export const getFollowers = (username, relation, page = 1) =>
  request(withQuery(`/users/${encodeURIComponent(username)}/${relation}/`, { page }));