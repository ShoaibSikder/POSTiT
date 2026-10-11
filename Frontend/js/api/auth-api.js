import { API_PATHS } from "../config.js";
import { request } from "./api-client.js";

export const getCurrentUser = () => request(API_PATHS.currentUser);

export const login = (identifier, password, remember = true) =>
  request(API_PATHS.login, {
    method: "POST",
    body: { identifier, password, remember },
  });

export const register = (details) =>
  request(API_PATHS.register, { method: "POST", body: details });

export const logout = () =>
  request(API_PATHS.logout, { method: "POST", body: {} });