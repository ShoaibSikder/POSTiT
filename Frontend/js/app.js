import { ensureAuthChecked } from "./services/auth-service.js";
import { renderNavigation, installTheme } from "./components/navbar.js";
import { showToast } from "./components/toast.js";

installTheme();

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey) {
    const target = event.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) return;
    event.preventDefault();
    document.querySelector(".global-search input")?.focus();
  }
});

export async function initShell() {
  let user = null;
  try {
    user = await ensureAuthChecked();
  } catch (error) {
    showToast(error.message, "error");
  }
  renderNavigation();
  return user;
}

export function requireSignIn(user) {
  if (user) return true;
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  showToast("Sign in to access this page.", "info");
  window.setTimeout(() => {
    window.location.assign(`login.html?next=${next}`);
  }, 700);
  return false;
}
