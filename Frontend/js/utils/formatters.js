import { API_ORIGIN } from "../config.js";

export function mediaUrl(value) {
  if (!value) return "";
  try {
    const url = new URL(value, API_ORIGIN);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
}

export function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[character];
  });
}

export function displayName(user = {}) {
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ").trim();
  return name || user.username || "POSTiT member";
}

export function initials(name = "") {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return (parts.length > 1
    ? `${parts[0][0]}${parts[1][0]}`
    : (parts[0] || "P").slice(0, 2)
  ).toUpperCase();
}

export function formatDate(value, options = {}) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    ...options,
  }).format(date);
}

export function timeAgo(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const units = [
    ["year", 31536000],
    ["month", 2592000],
    ["week", 604800],
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) {
      return new Intl.RelativeTimeFormat(undefined, { numeric: "auto" }).format(
        Math.round(seconds / size),
        unit,
      );
    }
  }
  return "just now";
}

export function avatarMarkup(user = {}, size = "") {
  const name = displayName(user);
  const avatar = mediaUrl(user.avatar || user.profile?.avatar);
  const classes = ["avatar", size].filter(Boolean).join(" ");
  if (avatar) {
    return `<img class="${classes}" src="${escapeHtml(avatar)}" alt="${escapeHtml(`${name}'s profile photo`)}" loading="lazy">`;
  }
  return `<span class="${classes} avatar-fallback" aria-label="${escapeHtml(name)}">${escapeHtml(initials(name))}</span>`;
}

export function errorMessage(error) {
  return error instanceof Error && error.message
    ? error.message
    : "Something went wrong. Please try again.";
}