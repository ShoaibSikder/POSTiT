import { initShell, requireSignIn } from "../app.js";
import { getNextPage, getResults } from "../api/api-client.js";
import { searchPosts, searchUsers } from "../api/search-api.js";
import { followUser, getFollowers, unfollowUser } from "../api/follows-api.js";
import { bindPostActions } from "../components/post-actions.js";
import { postCardMarkup } from "../components/post-card.js";
import { avatarMarkup, displayName, escapeHtml } from "../utils/formatters.js";
import { showToast } from "../components/toast.js";

const user = await initShell();
if (!requireSignIn(user)) throw new Error("Authentication required.");

const form = document.querySelector("#search-form");
const queryField = document.querySelector("#search-query");
const filters = document.querySelector("#post-filters");
const results = document.querySelector("#search-results");
const pagination = document.querySelector("#search-pagination");
const tabButtons = [...document.querySelectorAll("[data-search-type]")];
let type = "users";
let page = 1;
let nextPage = null;
let loadedPeople = [];
let following = new Set();
let followingLoad;
let searchTimer;
let activeSearch = 0;

function emptyMarkup(title, body) {
  return `<div class="empty-state"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p></div>`;
}

async function loadFollowing() {
  const names = new Set();
  let current = 1;
  while (current) {
    const data = await getFollowers(user.username, "following", current);
    getResults(data).forEach((item) => names.add(item.username));
    current = getNextPage(data);
  }
  return names;
}

function renderPeople(people) {
  if (!people.length) {
    const hasQuery = Boolean(queryField.value.trim());
    results.innerHTML = hasQuery
      ? emptyMarkup("No people found", "Try another username or search for a different name.")
      : emptyMarkup("No other people yet", "There are no other accounts to show right now.");
    return;
  }
  results.innerHTML = `<div class="people-results">${people.map((person) => `
    <article class="people-result section-card">
      <a class="people-result-person" href="profile.html?u=${encodeURIComponent(person.username)}">
        ${avatarMarkup(person, "avatar-small")}<span><strong>${escapeHtml(displayName(person))}</strong><small>@${escapeHtml(person.username)} · ${Number(person.follower_count || 0).toLocaleString()} followers</small></span>
      </a>
      ${person.username === user.username ? '<span class="muted small-copy">You</span>' : `<button class="button ${following.has(person.username) ? "button-secondary" : "button-primary"} button-small" type="button" data-follow-person="${escapeHtml(person.username)}" data-following="${following.has(person.username)}">${following.has(person.username) ? "Following" : "Follow"}</button>`}
    </article>`).join("")}</div>`;
  results.querySelectorAll("[data-follow-person]").forEach((button) => {
    button.addEventListener("click", toggleFollow);
  });
}

async function toggleFollow(event) {
  const button = event.currentTarget;
  const name = button.dataset.followPerson;
  const isFollowing = button.dataset.following === "true";
  button.disabled = true;
  try {
    const response = await (isFollowing ? unfollowUser(name) : followUser(name));
    button.dataset.following = String(response.following);
    button.textContent = response.following ? "Following" : "Follow";
    button.classList.toggle("button-primary", !response.following);
    button.classList.toggle("button-secondary", response.following);
    if (response.following) following.add(name);
    else following.delete(name);
    showToast(response.following ? `You’re now following @${name}.` : `You unfollowed @${name}.`, "success");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

function renderPagination() {
  pagination.innerHTML = nextPage
    ? `<button type="button" class="button button-secondary" data-load-more>Load more</button>`
    : "";
  pagination.querySelector("[data-load-more]")?.addEventListener("click", () => runSearch(nextPage, true));
}

async function runSearch(targetPage = 1, append = false) {
  const searchId = ++activeSearch;
  const q = queryField.value.trim();
  const values = new FormData(filters);
  const params = {
    q,
    author: values.get("author"),
    from: values.get("from"),
    to: values.get("to"),
  };
  if (type === "posts" && !q && !params.author && !params.from && !params.to) {
    results.innerHTML = emptyMarkup("Start with a search", "Add a word, username, or date range to find public posts.");
    pagination.innerHTML = "";
    return;
  }

  results.setAttribute("aria-busy", "true");
  if (!append) results.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Searching POSTiT…</div>';
  pagination.innerHTML = "";
  try {
    if (type === "users") {
      followingLoad ||= loadFollowing().catch((error) => {
        followingLoad = null;
        throw error;
      });
      following = await followingLoad;
    }
    const data = type === "posts"
      ? await searchPosts(params, targetPage)
      : await searchUsers(q, targetPage);
    if (searchId !== activeSearch) return;
    const items = getResults(data);
    page = targetPage;
    nextPage = getNextPage(data);
    if (type === "posts") {
      if (!append && !items.length) results.innerHTML = emptyMarkup("No posts found", "Try a broader phrase or adjust the author and date filters.");
      else if (append) results.insertAdjacentHTML("beforeend", items.map(postCardMarkup).join(""));
      else results.innerHTML = items.map(postCardMarkup).join("");
      bindPostActions(results, { onPostChanged: () => runSearch(page) });
    } else {
      loadedPeople = append ? [...loadedPeople, ...items] : items;
      renderPeople(loadedPeople);
    }
    renderPagination();
  } catch (error) {
    if (searchId !== activeSearch) return;
    results.innerHTML = `<div class="inline-error">${escapeHtml(error.message)} <button class="text-button" type="button" data-search-retry>Try again</button></div>`;
    results.querySelector("[data-search-retry]")?.addEventListener("click", () => runSearch(targetPage, append));
  } finally {
    if (searchId === activeSearch) results.removeAttribute("aria-busy");
  }
}

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  window.clearTimeout(searchTimer);
  runSearch();
});
function scheduleSearch() {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => runSearch(), 350);
}

queryField.addEventListener("input", scheduleSearch);
filters?.addEventListener("input", scheduleSearch);
filters?.addEventListener("change", (event) => {
  if (event.target.name === "date-range") {
    const from = filters.elements.namedItem("from");
    const to = filters.elements.namedItem("to");
    const today = new Date();
    const rangeStart = new Date(today);
    if (event.target.value === "week") rangeStart.setDate(today.getDate() - 7);
    if (event.target.value === "month") rangeStart.setMonth(today.getMonth() - 1);
    const formatDate = (date) =>
      `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    if (event.target.value === "week" || event.target.value === "month") {
      from.value = formatDate(rangeStart);
      to.value = formatDate(today);
    } else if (!event.target.value) {
      from.value = "";
      to.value = "";
    }
  } else if (event.target.name === "from" || event.target.name === "to") {
    filters.elements.namedItem("date-range").value = "custom";
  }
  scheduleSearch();
});
filters?.addEventListener("submit", (event) => {
  event.preventDefault();
  window.clearTimeout(searchTimer);
  runSearch();
});
tabButtons.forEach((button) => button.addEventListener("click", () => {
  window.clearTimeout(searchTimer);
  type = button.dataset.searchType;
  loadedPeople = [];
  tabButtons.forEach((item) => {
    const active = item === button;
    item.classList.toggle("is-active", active);
    item.setAttribute("aria-selected", String(active));
  });
  filters.hidden = type !== "posts";
  runSearch();
}));

const params = new URLSearchParams(window.location.search);
queryField.value = params.get("q") || "";
await runSearch();