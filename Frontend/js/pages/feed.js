import { initShell, requireSignIn } from "../app.js";
import { getFeed, createPost, getUserPosts } from "../api/posts-api.js";
import { getNextPage, getResults } from "../api/api-client.js";
import { followUser } from "../api/follows-api.js";
import { getUserSuggestions } from "../api/search-api.js";
import { icon } from "../components/icons.js";
import { postCardMarkup } from "../components/post-card.js";
import { bindPostActions } from "../components/post-actions.js";
import { showToast } from "../components/toast.js";
import { avatarMarkup, displayName, escapeHtml } from "../utils/formatters.js";
import { validateUploads } from "../services/upload-service.js";
import { getMyProfile } from "../api/profiles-api.js";

const user = await initShell();
const authorized = requireSignIn(user);

const list = document.querySelector("#feed-list");
const pagination = document.querySelector("#feed-pagination");
const composer = document.querySelector("#composer");
const content = document.querySelector("#post-content");
const files = document.querySelector("#post-images");
const preview = document.querySelector("#image-preview");
const count = document.querySelector("#post-count");
const composerError = document.querySelector("#composer-error");
let selectedImages = [];
let page = 1;
let nextPage = null;

if (authorized) {
  document.querySelector("[data-current-avatar]").innerHTML = avatarMarkup(user, "avatar-small");
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const name = displayName(user);
  document.querySelector("#feed-greeting").textContent = `${greeting}, ${name}`;
  content.placeholder = `What’s on your mind, ${name}?`;
  void loadFeedSidebar();
}

async function loadFeedSidebar() {
  const profileCard = document.querySelector("#feed-profile-card");
  const suggestions = document.querySelector("#people-suggestions");
  try {
    const [profile, postsData] = await Promise.all([
      getMyProfile(),
      getUserPosts(user.username),
    ]);
    const counts = [
      ["Posts", postsData.count ?? getResults(postsData).length],
      ["Followers", profile.follower_count ?? 0],
      ["Following", profile.following_count ?? 0],
    ];
    profileCard.querySelector("[data-mini-profile-avatar]").innerHTML =
      avatarMarkup(profile, "avatar-profile");
    profileCard.querySelector("[data-mini-profile-name]").textContent =
      displayName(profile);
    profileCard.querySelector("[data-mini-profile-username]").textContent =
      `@${profile.username}`;
    profileCard.querySelector("[data-mini-profile-bio]").textContent =
      profile.bio || "";
    profileCard.querySelector("[data-mini-profile-counts]").innerHTML =
      counts.map(([label, value]) => `
        <div><b>${Number(value).toLocaleString()}</b><span>${label}</span></div>
      `).join("");
  } catch (error) {
    profileCard.querySelector(".mini-profile-content").innerHTML =
      `<p class="inline-error">Could not load your account summary: ${escapeHtml(error.message)}</p>`;
  }

  try {
    const people = getResults(await getUserSuggestions());
    suggestions.innerHTML = people.length
      ? people.slice(0, 4).map((person) => `
        <div class="people-suggestion" data-suggestion="${escapeHtml(person.username)}">
          <a class="people-suggestion-profile" href="profile.html?u=${encodeURIComponent(person.username)}">
            ${avatarMarkup(person, "avatar-small")}
            <span><strong>${escapeHtml(displayName(person))}</strong><small>@${escapeHtml(person.username)}</small></span>
          </a>
          <button class="button button-secondary button-small" type="button" data-follow-suggestion="${escapeHtml(person.username)}">Follow</button>
          <p class="form-error" data-follow-error role="alert"></p>
        </div>
      `).join("")
      : '<p class="small-copy">You’re all caught up. Search for people to discover more.</p>';
  } catch (error) {
    suggestions.innerHTML =
      `<p class="inline-error">Could not load suggestions: ${escapeHtml(error.message)}</p>`;
  }

  suggestions.querySelectorAll("[data-follow-suggestion]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = button.closest("[data-suggestion]");
      button.disabled = true;
      try {
        await followUser(button.dataset.followSuggestion);
        row.remove();
        showToast(`You’re now following @${button.dataset.followSuggestion}.`, "success");
        void loadFeedSidebar();
      } catch (error) {
        row.querySelector("[data-follow-error]").textContent = error.message;
        button.disabled = false;
      }
    });
  });
}

async function loadFeed(targetPage = 1, append = false) {
  if (!append) {
    list.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Gathering your feed…</div>';
  }
  pagination.innerHTML = "";
  try {
    const data = await getFeed(targetPage);
    const posts = getResults(data);
    page = targetPage;
    nextPage = getNextPage(data);
    if (!append && posts.length === 0) {
      list.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon("compass")}</div><h3>Your feed is ready for a first hello</h3><p>Follow a few people to see their posts here, or share something of your own.</p><a class="button button-primary" href="search.html">Find people to follow</a></div>`;
    } else if (append) {
      list.insertAdjacentHTML("beforeend", posts.map(postCardMarkup).join(""));
    } else {
      list.innerHTML = posts.map(postCardMarkup).join("");
    }
    document.querySelector("#feed-status").textContent = "Feed is up to date";
    if (nextPage) {
      pagination.innerHTML = `<button class="button button-secondary" type="button" data-next-page>Show more posts</button>`;
      pagination.querySelector("[data-next-page]").addEventListener("click", () => loadFeed(nextPage, true));
    }
  } catch (error) {
    document.querySelector("#feed-status").textContent = "Could not refresh your feed";
    list.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${icon("compass")}</div><h3>We couldn’t load your feed</h3><p>${escapeHtml(error.message)}</p><button class="button button-secondary" type="button" data-feed-retry>Try again</button></div>`;
    list.querySelector("[data-feed-retry]")?.addEventListener("click", () => loadFeed());
  }
}

function renderPreview() {
  preview.replaceChildren();
  preview.hidden = selectedImages.length === 0;
  for (const file of selectedImages) {
    const image = document.createElement("img");
    image.src = URL.createObjectURL(file);
    image.alt = `Selected image: ${file.name}`;
    image.onload = () => URL.revokeObjectURL(image.src);
    preview.append(image);
  }
}

if (authorized) {
  content.addEventListener("input", () => {
    count.textContent = `${content.value.length.toLocaleString()} / 2,000`;
  });

  files.addEventListener("change", () => {
    const images = Array.from(files.files || []);
    const error = validateUploads(images);
    if (error) {
      composerError.textContent = error;
      files.value = "";
      return;
    }
    composerError.textContent = "";
    selectedImages = images;
    renderPreview();
  });

  composer.addEventListener("submit", async (event) => {
    event.preventDefault();
    composerError.textContent = "";
    const text = content.value.trim();
    if (!text && !selectedImages.length) {
      composerError.textContent = "Add a thought or choose a photo before sharing.";
      return;
    }
    const submit = composer.querySelector("#post-submit");
    submit.disabled = true;
    submit.textContent = "Sharing…";
    try {
      await createPost({ content: text, images: selectedImages });
      content.value = "";
      count.textContent = "0 / 2,000";
      files.value = "";
      selectedImages = [];
      renderPreview();
      showToast("Your moment has been shared.", "success");
      await loadFeed();
    } catch (error) {
      composerError.textContent = error.message;
    } finally {
      submit.disabled = false;
      submit.textContent = "Post";
    }
  });

  bindPostActions(list, { onPostChanged: () => loadFeed(page) });
}

if (authorized) await loadFeed();