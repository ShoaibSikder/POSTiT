import { getCachedUser } from "../services/auth-service.js";
import { avatarMarkup, displayName, escapeHtml } from "../utils/formatters.js";
import { getNotifications } from "../api/notifications-api.js";
import { showToast } from "./toast.js";
import { icon, logoMarkup } from "./icons.js";

const navLinks = [
  ["Home", "../pages/feed.html", "home", "home"],
  ["Search", "../pages/search.html", "compass", "search"],
  ["Notifications", "../pages/notifications.html", "bell", "notifications"],
  ["Profile", "../pages/profile.html", "user", "profile"],
];

function currentPage() {
  const file = window.location.pathname.split("/").pop();
  if (file === "index.html" || file === "feed.html" || !file) return "home";
  return file.replace(".html", "");
}

function navItem([label, href, iconName, key], current, compact = false) {
  const active = current === key;
  return `<a class="nav-link ${active ? "is-active" : ""} ${compact ? "nav-link-compact" : ""}" href="${href}" ${active ? 'aria-current="page"' : ""}>${icon(iconName)}<span>${label}</span></a>`;
}

function themeButton() {
  return `<button class="icon-button theme-toggle" type="button" data-theme-toggle aria-label="Switch color theme" title="Switch color theme">${icon("moon")}</button>`;
}

function renderAdminLink(user) {
  return user?.role === "admin"
    ? `<a class="nav-link" href="../pages/admin.html">${icon("shield")}<span>Administrator console</span></a>`
    : "";
}

export function setTheme(theme) {
  const next = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  document.documentElement.style.colorScheme = next;
  window.localStorage.setItem("postit-theme", next);
  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.innerHTML = icon(next === "dark" ? "sun" : "moon");
    button.setAttribute(
      "aria-label",
      `Switch to ${next === "dark" ? "light" : "dark"} theme`,
    );
  });
}

export function installTheme() {
  const saved = window.localStorage.getItem("postit-theme");
  const preferred =
    window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  setTheme(saved || (preferred ? "dark" : "light"));
  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-theme-toggle]");
    if (toggle) {
      setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
    }
  });
}

export function renderNavigation() {
  const user = getCachedUser();
  const current = currentPage();
  const authPage = ["login", "register"].includes(current);
  const sidebar = document.querySelector("[data-sidebar]");
  const topbar = document.querySelector("[data-topbar]");
  const mobile = document.querySelector("[data-mobile-nav]");

  if (sidebar) {
    sidebar.innerHTML = authPage
      ? `<div class="sidebar-welcome"><span class="eyebrow">A place to be</span><h2>Share moments.<br>Find your people.</h2><p>Stories worth sharing start with a hello.</p></div>`
      : `
      <nav class="primary-nav" aria-label="Primary navigation">${navLinks.filter(([, , , key]) => key !== "profile").map((item) => navItem(item, current)).join("")}</nav>
           ${renderAdminLink(user)}
           <div class="sidebar-bottom">
             ${user ? `<button class="nav-link nav-action" type="button" data-signout>${icon("logout")}<span>Sign out</span></button>` : `<a class="button button-secondary button-wide" href="../pages/login.html">Sign in</a><a class="sidebar-signup" href="../pages/register.html">Create an account</a>`}
           </div>`;
  }

  if (topbar) {
    topbar.innerHTML = authPage
      ? `<div class="topbar-mobile-brand">${logoMarkup()}</div><div class="topbar-actions">${themeButton()}</div>`
      : `
      <div class="topbar-mobile-brand">${logoMarkup()}</div>
      <form class="global-search" action="../pages/search.html" role="search">
        ${icon("search")}<input type="search" name="q" placeholder="Search people or posts" aria-label="Search POSTiT"><kbd>/</kbd>
      </form>
      <div class="topbar-actions">
        ${themeButton()}
        <a class="icon-button topbar-notification" href="../pages/notifications.html" aria-label="Notifications"><span class="notification-icon">${icon("bell")}</span><span class="notification-count" data-unread-badge hidden></span></a>
        ${user ? `
        <div class="topbar-profile-menu">
          <button class="topbar-user" type="button" data-profile-menu-toggle aria-expanded="false" aria-controls="topbar-profile-dropdown" aria-label="Account options">
            ${avatarMarkup(user, "avatar-small")}
            <span class="topbar-user-name">${escapeHtml(displayName(user))}</span>
          </button>
          <div class="profile-dropdown" id="topbar-profile-dropdown" hidden>
            <a href="../pages/profile.html">${icon("user")}<span>Profile</span></a>
            <button type="button" data-signout>${icon("logout")}<span>Sign out</span></button>
          </div>
        </div>` : `<a class="button button-primary topbar-login" href="../pages/login.html">Log in</a>`}
      </div>`;
    const input = topbar.querySelector('input[name="q"]');
    if (input) {
      input.value = new URLSearchParams(window.location.search).get("q") || "";
    }
    if (user && !authPage) {
      void updateNotificationBadge(topbar);
    }
  }

  if (mobile) {
    mobile.innerHTML = authPage ? "" : navLinks.map((item) => navItem(item, current, true)).join("");
  }

  const profileMenu = topbar?.querySelector(".profile-dropdown");
  const profileMenuToggle = topbar?.querySelector("[data-profile-menu-toggle]");
  document.addEventListener("click", async (event) => {
    const toggle = event.target.closest("[data-profile-menu-toggle]");
    if (toggle && profileMenu) {
      profileMenu.hidden = !profileMenu.hidden;
      toggle.setAttribute("aria-expanded", String(!profileMenu.hidden));
      return;
    }
    if (profileMenu && !profileMenu.hidden && !profileMenu.contains(event.target)) {
      profileMenu.hidden = true;
      profileMenuToggle?.setAttribute("aria-expanded", "false");
    }

    const unavailable = event.target.closest("[data-unavailable]");
    if (unavailable) {
      showToast(`${unavailable.dataset.unavailable} are not available yet.`, "info");
    }
    if (event.target.closest("[data-signout]")) {
      event.preventDefault();
      try {
        const { signOut } = await import("../services/auth-service.js");
        await signOut();
        window.location.assign("../index.html");
      } catch (error) {
        showToast(error.message || "Could not sign out. Try again.", "error");
      }
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && profileMenu && !profileMenu.hidden) {
      profileMenu.hidden = true;
      profileMenuToggle?.setAttribute("aria-expanded", "false");
      profileMenuToggle?.focus();
    }
  });
}

async function updateNotificationBadge(topbar) {
  const badge = topbar.querySelector("[data-unread-badge]");
  const notificationLink = topbar.querySelector(".topbar-notification");
  if (!badge || !notificationLink) return;
  try {
    const { unread } = await getNotifications();
    const unreadCount = Number(unread);
    if (!Number.isFinite(unreadCount)) {
      throw new Error("The unread notification count was not valid.");
    }
    if (unreadCount > 0) {
      badge.textContent = unreadCount > 99 ? "99+" : String(unreadCount);
      badge.hidden = false;
      notificationLink.setAttribute(
        "aria-label",
        `Notifications, ${unreadCount} unread`,
      );
    }
  } catch (error) {
    showToast(error.message || "Could not load your notification count.", "error");
  }
}