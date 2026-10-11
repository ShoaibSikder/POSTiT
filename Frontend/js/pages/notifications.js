import { initShell, requireSignIn } from "../app.js";
import { getNextPage, getResults } from "../api/api-client.js";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../api/notifications-api.js";
import { avatarMarkup, escapeHtml, timeAgo } from "../utils/formatters.js";
import { showToast } from "../components/toast.js";

const user = await initShell();
if (!requireSignIn(user)) throw new Error("Authentication required.");

const list = document.querySelector("#notification-list");
const pagination = document.querySelector("#notification-pagination");
const markAll = document.querySelector("#mark-all-read");
let page = 1;
let nextPage = null;

function actionText(notification) {
  if (notification.type === "follow") return "started following you";
  if (notification.type === "like") return "appreciated your post";
  if (notification.type === "comment") return "commented on your post";
  return "interacted with you";
}

function render(items, append = false) {
  if (!append && items.length === 0) {
    list.innerHTML = '<div class="empty-state"><h3>You’re all caught up</h3><p>When someone follows you or interacts with your posts, you’ll see it here.</p></div>';
    return;
  }
  const html = items.map((item) => `
    <article class="notification-item ${item.is_read ? "" : "is-unread"}" data-notification-id="${item.id}">
      <a class="notification-avatar" href="profile.html?u=${encodeURIComponent(item.actor || "")}">${avatarMarkup({ username: item.actor, avatar: item.actor_avatar }, "avatar-small")}</a>
      <div class="notification-copy"><p><a href="profile.html?u=${encodeURIComponent(item.actor || "")}"><strong>${escapeHtml(item.actor || "A POSTiT member")}</strong></a> ${escapeHtml(actionText(item))}.</p><time class="muted" datetime="${escapeHtml(item.created_at)}">${escapeHtml(timeAgo(item.created_at))}</time></div>
      ${item.is_read ? '<span class="notification-read-label">Read</span>' : `<button class="button button-secondary button-small" type="button" data-mark-read="${item.id}">Mark read</button>`}
    </article>`).join("");
  if (append) list.insertAdjacentHTML("beforeend", html);
  else list.innerHTML = html;
  list.querySelectorAll("[data-mark-read]").forEach((button) => button.addEventListener("click", markRead));
}

function renderPagination() {
  pagination.innerHTML = nextPage
    ? '<button class="button button-secondary" type="button" data-load-notifications>Load more</button>'
    : "";
  pagination.querySelector("[data-load-notifications]")?.addEventListener("click", loadMore);
}

async function load(pageNumber = 1, append = false) {
  if (!append) list.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Loading notifications…</div>';
  pagination.innerHTML = "";
  try {
    const data = await getNotifications(pageNumber);
    const items = getResults(data);
    page = pageNumber;
    nextPage = getNextPage(data);
    render(items, append);
    renderPagination();
    markAll.disabled = !Number(data?.unread);
  } catch (error) {
    list.innerHTML = `<div class="inline-error">${escapeHtml(error.message)} <button class="text-button" type="button" data-retry-notifications>Try again</button></div>`;
    list.querySelector("[data-retry-notifications]")?.addEventListener("click", () => load(pageNumber, append));
    markAll.disabled = true;
  }
}

async function loadMore() {
  if (!nextPage) return;
  const button = pagination.querySelector("[data-load-notifications]");
  button.disabled = true;
  try {
    await load(nextPage, true);
  } finally {
    if (button.isConnected) button.disabled = false;
  }
}

async function markRead(event) {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await markNotificationRead(button.dataset.markRead);
    const row = button.closest("[data-notification-id]");
    row.classList.remove("is-unread");
    button.replaceWith(Object.assign(document.createElement("span"), {
      className: "notification-read-label",
      textContent: "Read",
    }));
    showToast("Notification marked as read.", "success");
    await load(page);
  } catch (error) {
    button.disabled = false;
    showToast(error.message, "error");
  }
}

markAll?.addEventListener("click", async () => {
  markAll.disabled = true;
  try {
    await markAllNotificationsRead();
    showToast("All notifications marked as read.", "success");
    await load(1);
  } catch (error) {
    showToast(error.message, "error");
    markAll.disabled = false;
  }
});

await load();