import { initShell, requireSignIn } from "../app.js";
import {
  deleteAdminComment,
  deleteAdminMedia,
  deleteAdminNotification,
  deleteAdminPost,
  getAdminActivity,
  getAdminAudit,
  getAdminComments,
  getAdminDashboard,
  getAdminMedia,
  getAdminNotifications,
  getAdminPosts,
  getAdminRelationships,
  getAdminSettings,
  getAdminUsers,
  moderateUser,
  updateAdminSetting,
} from "../api/admin-api.js";
import { getNextPage, getResults } from "../api/api-client.js";
import { openTextDialog } from "../components/modal.js";
import { avatarMarkup, escapeHtml, formatDate, timeAgo } from "../utils/formatters.js";
import { showToast } from "../components/toast.js";

const user = await initShell();
if (!requireSignIn(user)) throw new Error("Authentication required.");

const content = document.querySelector("#admin-content");
const tabs = [...document.querySelectorAll("[data-admin-tab]")];
let section = "overview";
let page = 1;
let subSection = "posts";
let mediaType = "post";
let userQuery = "";

if (user?.role !== "admin") {
  content.innerHTML = '<div class="empty-state"><h2>Administrator access required</h2><p>This area is restricted to platform administrators.</p><a class="button button-secondary" href="feed.html">Return to your feed</a></div>';
} else {
  tabs.forEach((tab) => tab.addEventListener("click", () => {
    section = tab.dataset.adminTab;
    page = 1;
    tabs.forEach((item) => {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    loadSection();
  }));
  await loadSection();
}

function tableMarkup(headers, rows, emptyMessage = "No records to show.") {
  return `<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${rows || `<tr><td colspan="${headers.length}" class="muted">${escapeHtml(emptyMessage)}</td></tr>`}</tbody></table></div>`;
}

function actionButton(label, action, id, danger = false) {
  return `<button class="admin-action ${danger ? "danger" : ""}" type="button" data-admin-action="${escapeHtml(action)}" data-record-id="${id}">${escapeHtml(label)}</button>`;
}

function paginationMarkup(next, previous) {
  if (!next && !previous) return "";
  return `<div class="pagination">${previous ? '<button type="button" class="button button-secondary" data-page-prev>Previous</button>' : ""}${next ? '<button type="button" class="button button-secondary" data-page-next>Next</button>' : ""}</div>`;
}

function wirePagination(next, previous) {
  content.querySelector("[data-page-prev]")?.addEventListener("click", () => {
    page = previous;
    loadSection();
  });
  content.querySelector("[data-page-next]")?.addEventListener("click", () => {
    page = next;
    loadSection();
  });
}

function renderPage(data) {
  const next = getNextPage(data);
  const previous = data?.previous
    ? Math.max(1, Number(new URL(data.previous, window.location.href).searchParams.get("page") || page - 1))
    : null;
  content.insertAdjacentHTML("beforeend", paginationMarkup(next, previous));
  wirePagination(next, previous);
}

async function loadSection() {
  content.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Loading admin tools…</div>';
  try {
    if (section === "overview") await showOverview();
    else if (section === "users") await showUsers();
    else if (section === "content") await showContent();
    else if (section === "media") await showMedia();
    else if (section === "notifications") await showNotifications();
    else if (section === "relationships") await showRelationships();
    else if (section === "audit") await showAudit();
    else if (section === "settings") await showSettings();
  } catch (error) {
    content.innerHTML = `<div class="inline-error">${escapeHtml(error.message)} <button class="text-button" type="button" data-admin-retry>Try again</button></div>`;
    content.querySelector("[data-admin-retry]")?.addEventListener("click", loadSection);
  }
}

async function showOverview() {
  const [data, activity] = await Promise.all([getAdminDashboard(), getAdminActivity({})]);
  const metrics = [
    ["People", data.counts.users],
    ["Active accounts", data.counts.active_users],
    ["Posts", data.counts.posts],
    ["Comments", data.counts.comments],
    ["Appreciations", data.counts.likes],
    ["Follows", data.counts.follows],
    ["Post photos", data.counts.post_images],
    ["Profile photos", data.counts.profile_media],
    ["Unread alerts", data.counts.unread_notifications],
    ["Searches · 24h", data.counts.searches_24h],
  ];
  const recent = (data.recent_admin_activity || []).map((item) => `<tr><td>${escapeHtml(item.admin)}</td><td>${escapeHtml(item.action.replaceAll("_", " "))}</td><td>${escapeHtml(item.target_type)} #${item.target_id}</td><td>${escapeHtml(timeAgo(item.created_at))}</td></tr>`).join("");
  const activityRows = Object.entries(activity.stats || {}).map(([name, days]) =>
    `<tr><td>${escapeHtml(name)}</td><td>${days.reduce((sum, day) => sum + Number(day.count), 0).toLocaleString()}</td><td>${days.length ? `${escapeHtml(formatDate(days[0]["created_at__date"]))} – ${escapeHtml(formatDate(days[days.length - 1]["created_at__date"]))}` : "No recent activity"}</td></tr>`,
  ).join("");
  content.innerHTML = `<div class="admin-overview">${metrics.map(([label, value]) => `<article class="admin-metric section-card"><span>${escapeHtml(label)}</span><strong>${Number(value || 0).toLocaleString()}</strong></article>`).join("")}</div>
    <section class="section-card admin-section"><h2>Recent admin actions</h2>${tableMarkup(["Administrator", "Action", "Target", "When"], recent, "No admin actions have been recorded.")}</section>
    <section class="section-card admin-section"><h2>Platform activity</h2>${tableMarkup(["Activity", "Events", "Dates"], activityRows, "No platform activity yet.")}</section>`;
}

async function showUsers() {
  const data = await getAdminUsers({ q: userQuery, page });
  const rows = getResults(data).map((item) => {
    const state = item.is_banned ? "Banned" : item.is_active ? "Active" : "Inactive";
    const action = item.is_banned
      ? actionButton("Unban", "unban", item.id)
      : item.is_active
        ? actionButton("Ban", "ban", item.id, true) + actionButton("Deactivate", "deactivate", item.id, true)
        : actionButton("Activate", "activate", item.id);
    return `<tr><td><span class="admin-user-cell">${avatarMarkup(item, "avatar-small")}<strong>${escapeHtml(item.username)}</strong></span></td><td>${escapeHtml(item.email)}</td><td>${escapeHtml(item.role)}</td><td>${state}</td><td>${escapeHtml(formatDate(item.date_joined))}</td><td><div class="admin-actions">${action}</div></td></tr>`;
  }).join("");
  content.innerHTML = `<section class="section-card admin-section"><div class="admin-toolbar"><h2>People</h2><form class="admin-filter" data-user-search><input name="q" value="${escapeHtml(userQuery)}" placeholder="Search username or email" aria-label="Search users"><button class="button button-secondary button-small">Search</button></form></div>${tableMarkup(["Account", "Email", "Role", "Status", "Joined", "Actions"], rows, "No matching accounts.")}</section>`;
  content.querySelector("[data-user-search]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    userQuery = new FormData(event.currentTarget).get("q").trim();
    page = 1;
    loadSection();
  });
  bindAdminActions();
  renderPage(data);
}

async function showContent() {
  const data = subSection === "posts" ? await getAdminPosts(page) : await getAdminComments(page);
  const items = getResults(data);
  const rows = subSection === "posts"
    ? items.map((post) => `<tr><td>#${post.id}</td><td>@${escapeHtml(post.author)}</td><td>${escapeHtml((post.content || "Photo post").slice(0, 140))}</td><td>${escapeHtml(timeAgo(post.created_at))}</td><td>${actionButton("Remove", "delete-post", post.id, true)}</td></tr>`).join("")
    : items.map((comment) => `<tr><td>#${comment.id}</td><td>@${escapeHtml(comment.author)}</td><td>${escapeHtml(comment.content.slice(0, 140))}</td><td>#${comment.post}</td><td>${actionButton("Remove", "delete-comment", comment.id, true)}</td></tr>`).join("");
  content.innerHTML = `<section class="section-card admin-section"><div class="admin-toolbar"><h2>Content moderation</h2><div class="admin-filter"><button class="admin-action ${subSection === "posts" ? "is-active" : ""}" type="button" data-content-type="posts">Posts</button><button class="admin-action ${subSection === "comments" ? "is-active" : ""}" type="button" data-content-type="comments">Comments</button></div></div>${tableMarkup(subSection === "posts" ? ["ID", "Author", "Content", "Created", "Actions"] : ["ID", "Author", "Comment", "Post", "Actions"], rows, "No content to show.")}</section>`;
  content.querySelectorAll("[data-content-type]").forEach((button) => button.addEventListener("click", () => {
    subSection = button.dataset.contentType;
    page = 1;
    loadSection();
  }));
  bindAdminActions();
  renderPage(data);
}

async function showMedia() {
  const data = await getAdminMedia(mediaType, page);
  const rows = getResults(data).map((item) => `<tr><td><img class="admin-media-thumb" src="${escapeHtml(item.url)}" alt="Uploaded by ${escapeHtml(item.owner)}" loading="lazy"></td><td>@${escapeHtml(item.owner)}</td><td>${escapeHtml(item.media_type)} · #${item.id}</td><td>${escapeHtml(timeAgo(item.created_at))}</td><td>${actionButton("Remove", "delete-media", item.id, true)}</td></tr>`).join("");
  content.innerHTML = `<section class="section-card admin-section"><div class="admin-toolbar"><h2>Uploaded media</h2><div class="admin-filter"><button class="admin-action ${mediaType === "post" ? "is-active" : ""}" type="button" data-media-type="post">Post photos</button><button class="admin-action ${mediaType === "profile" ? "is-active" : ""}" type="button" data-media-type="profile">Profile photos</button></div></div>${tableMarkup(["Preview", "Owner", "Type", "Uploaded", "Actions"], rows, "No uploaded media to show.")}</section>`;
  content.querySelectorAll("[data-media-type]").forEach((button) => button.addEventListener("click", () => {
    mediaType = button.dataset.mediaType;
    page = 1;
    loadSection();
  }));
  bindAdminActions();
  renderPage(data);
}

async function showNotifications() {
  const data = await getAdminNotifications({ page });
  const rows = getResults(data).map((item) => `<tr><td>#${item.id}</td><td>@${escapeHtml(item.actor || "removed user")}</td><td>${escapeHtml(item.type)}</td><td>${item.is_read ? "Read" : "Unread"}</td><td>${actionButton("Remove", "delete-notification", item.id, true)}</td></tr>`).join("");
  content.innerHTML = `<section class="section-card admin-section"><h2>Notifications</h2>${tableMarkup(["ID", "Actor", "Type", "Status", "Actions"], rows, "No notifications to show.")}</section>`;
  bindAdminActions();
  renderPage(data);
}

async function showRelationships() {
  const data = await getAdminRelationships();
  const rows = (data.recent || []).map((item) => `<tr><td>@${escapeHtml(item.follower)}</td><td>@${escapeHtml(item.following)}</td><td>${escapeHtml(timeAgo(item.created_at))}</td></tr>`).join("");
  content.innerHTML = `<div class="admin-overview"><article class="admin-metric section-card"><span>Total relationships</span><strong>${Number(data.total_relationships || 0).toLocaleString()}</strong></article><article class="admin-metric section-card"><span>New in 24 hours</span><strong>${Number(data.new_relationships_24h || 0).toLocaleString()}</strong></article></div><section class="section-card admin-section"><h2>Recent follows</h2>${tableMarkup(["Follower", "Following", "When"], rows, "No follows have been recorded.")}</section>`;
}

async function showAudit() {
  const data = await getAdminAudit({ page });
  const rows = getResults(data).map((item) => `<tr><td>@${escapeHtml(item.admin)}</td><td>${escapeHtml(item.action.replaceAll("_", " "))}</td><td>${escapeHtml(item.target_type)} #${item.target_id}</td><td>${escapeHtml(JSON.stringify(item.details || {}))}</td><td>${escapeHtml(timeAgo(item.created_at))}</td></tr>`).join("");
  content.innerHTML = `<section class="section-card admin-section"><h2>Audit log</h2>${tableMarkup(["Administrator", "Action", "Target", "Details", "When"], rows, "No audit records have been created.")}</section>`;
  renderPage(data);
}

const settingLabels = {
  POSTIT_MAX_IMAGE_SIZE_BYTES: ["Maximum image size (bytes)", 52428800],
  POSTIT_MAX_POST_IMAGES: ["Maximum images per post", 10],
  POSTIT_MAX_PROFILE_MEDIA: ["Maximum profile photos", 50],
  POSTIT_MAX_POST_LENGTH: ["Maximum post length", 10000],
  POSTIT_MAX_COMMENT_LENGTH: ["Maximum comment length", 5000],
};

async function showSettings() {
  const settings = await getAdminSettings();
  const rows = Object.entries(settingLabels).map(([key, [label, max]]) => `<tr><td>${escapeHtml(label)}<small class="muted">${escapeHtml(key)}</small></td><td><form class="admin-setting-form" data-setting="${escapeHtml(key)}"><input name="value" type="number" min="1" max="${max}" value="${Number(settings[key])}" required aria-label="${escapeHtml(label)}"><button class="button button-secondary button-small" type="submit">Save</button></form></td></tr>`).join("");
  content.innerHTML = `<section class="section-card admin-section"><h2>Platform limits</h2><p class="muted">Updates apply through the backend and are recorded in the audit log.</p>${tableMarkup(["Setting", "Value"], rows)}</section>`;
  content.querySelectorAll("[data-setting]").forEach((form) => form.addEventListener("submit", saveSetting));
}

async function moderationReason(action) {
  return openTextDialog({
    title: "Confirm moderation action",
    description: `This ${action} will be recorded in the moderation audit log. Provide a short reason.`,
    placeholder: "Reason for this moderation action",
    submitLabel: "Continue",
    maxLength: 500,
  });
}

function bindAdminActions() {
  content.querySelectorAll("[data-admin-action]").forEach((button) => button.addEventListener("click", moderateRecord));
}

async function moderateRecord(event) {
  const button = event.currentTarget;
  const action = button.dataset.adminAction;
  const reason = await moderationReason(action.replaceAll("-", " "));
  if (!reason) return;
  if (!reason.trim()) {
    showToast("A non-empty reason is required for moderation.", "error");
    return;
  }
  button.disabled = true;
  try {
    const id = button.dataset.recordId;
    if (["ban", "unban", "deactivate", "activate"].includes(action)) await moderateUser(id, action, reason);
    else if (action === "delete-post") await deleteAdminPost(id, reason);
    else if (action === "delete-comment") await deleteAdminComment(id, reason);
    else if (action === "delete-notification") await deleteAdminNotification(id, reason);
    else if (action === "delete-media") await deleteAdminMedia(mediaType, id, reason);
    showToast("Moderation action completed.", "success");
    await loadSection();
  } catch (error) {
    showToast(error.message, "error");
    button.disabled = false;
  }
}

async function saveSetting(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('[type="submit"]');
  const value = Number(new FormData(form).get("value"));
  button.disabled = true;
  try {
    await updateAdminSetting(form.dataset.setting, value);
    showToast("Platform setting updated.", "success");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}
