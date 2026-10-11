import { API_PATHS } from "../config.js";
import { request, withQuery } from "./api-client.js";

export const searchUsers = (q, page = 1) =>
  request(withQuery(API_PATHS.searchUsers, { q, page }));

export const searchPosts = (filters, page = 1) =>
  request(withQuery(API_PATHS.searchPosts, { ...filters, page }));

export const getUserSuggestions = (page = 1) =>
  request(withQuery("/search/suggestions/", { page }));