const configuredOrigin = new URLSearchParams(window.location.search).get("api");
const savedOrigin = window.localStorage.getItem("postit-api-origin");

export const API_ORIGIN = (configuredOrigin || savedOrigin || "http://127.0.0.1:8000")
  .trim()
  .replace(/\/+$/, "");

if (configuredOrigin) {
  window.localStorage.setItem("postit-api-origin", API_ORIGIN);
}

export const API_BASE_URL = `${API_ORIGIN}/api/v1`;
export const API_PATHS = {
  csrf: "/auth/csrf/",
  register: "/auth/register/",
  login: "/auth/login/",
  logout: "/auth/logout/",
  currentUser: "/auth/me/",
  feed: "/feed/",
  posts: "/posts/",
  profile: "/profiles/me/",
  notifications: "/notifications/",
  searchUsers: "/search/users/",
  searchPosts: "/search/posts/",
  adminDashboard: "/admin/dashboard/",
};
