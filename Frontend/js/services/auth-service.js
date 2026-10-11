import { getCurrentUser, login, logout, register } from "../api/auth-api.js";

let currentUser = null;
let authChecked = false;

export function getCachedUser() {
  return currentUser;
}

export async function refreshCurrentUser() {
  try {
    currentUser = await getCurrentUser();
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      currentUser = null;
    } else {
      throw error;
    }
  }
  authChecked = true;
  window.dispatchEvent(new CustomEvent("postit:auth", { detail: currentUser }));
  return currentUser;
}

export async function ensureAuthChecked() {
  if (authChecked) return currentUser;
  return refreshCurrentUser();
}

export async function signIn(identifier, password, remember = true) {
  currentUser = await login(identifier, password, remember);
  authChecked = true;
  window.dispatchEvent(new CustomEvent("postit:auth", { detail: currentUser }));
  return currentUser;
}

export async function signUp(details) {
  currentUser = await register(details);
  authChecked = true;
  window.dispatchEvent(new CustomEvent("postit:auth", { detail: currentUser }));
  return currentUser;
}

export async function signOut() {
  await logout();
  currentUser = null;
  authChecked = true;
  window.dispatchEvent(new CustomEvent("postit:auth", { detail: null }));
  return null;
}