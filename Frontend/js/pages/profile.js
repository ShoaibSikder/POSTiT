import { initShell, requireSignIn } from "../app.js";
import { getNextPage, getResults } from "../api/api-client.js";
import { followUser, getFollowers, unfollowUser } from "../api/follows-api.js";
import {
  addProfileMedia,
  deleteProfileMedia,
  getMyProfile,
  getUserMedia,
  getUserProfile,
  updateProfile,
} from "../api/profiles-api.js";
import { getUserPosts } from "../api/posts-api.js";
import { bindPostActions } from "../components/post-actions.js";
import { confirmDialog } from "../components/modal.js";
import { postCardMarkup } from "../components/post-card.js";
import { showToast } from "../components/toast.js";
import { avatarMarkup, displayName, escapeHtml, formatDate, mediaUrl as resolveMediaUrl } from "../utils/formatters.js";

const user = await initShell();
if (!requireSignIn(user)) throw new Error("Authentication required.");

const root = document.querySelector("#profile-root");
const username = new URLSearchParams(window.location.search).get("u") || user.username;
const isOwner = username === user.username;
let mediaPage = null;
let postPage = null;

function mediaUrl(value) {
  return resolveMediaUrl(value);
}

function imageMarkup(value, alt, className = "") {
  const src = mediaUrl(value);
  return src
    ? `<img${className ? ` class="${className}"` : ""} src="${escapeHtml(src)}" alt="${escapeHtml(alt)}" loading="lazy">`
    : "";
}

function mediaCardMarkup(item) {
  return `<figure class="profile-media-card" data-media-id="${item.id}">
    ${imageMarkup(item.image, item.caption || `${username}'s photo`)}
    ${item.caption ? `<figcaption>${escapeHtml(item.caption)}</figcaption>` : ""}
    ${isOwner ? `<button type="button" class="button button-danger button-small" data-delete-media="${item.id}">Remove</button>` : ""}
  </figure>`;
}

function profileMarkup(data, media, posts, postCount) {
  const name = displayName(data);
  const cover = imageMarkup(data.cover_image, `${name}'s cover`, "profile-cover-image");
  const avatar = avatarMarkup(data, "avatar-profile");
  root.innerHTML = `
    <section class="profile-page">
      <div class="profile-cover">${cover}</div>
      <header class="profile-header section-card">
        <div class="profile-identity">${avatar}<div><h1>${escapeHtml(name)}</h1><p class="muted">@${escapeHtml(data.username)}</p><p class="profile-bio">${escapeHtml(data.bio || "No bio yet.")}</p></div></div>
        <div class="profile-actions">${isOwner
          ? '<button class="button button-secondary" type="button" data-edit-profile>Edit profile</button>'
          : `<button class="button button-primary" type="button" data-follow-user="${escapeHtml(data.username)}">Follow</button>`}</div>
        <div class="profile-metrics"><span><strong data-profile-post-count>${Number(postCount || 0).toLocaleString()}</strong> posts</span><span><strong data-follower-count>${Number(data.follower_count || 0).toLocaleString()}</strong> followers</span><span><strong>${Number(data.following_count || 0).toLocaleString()}</strong> following</span></div>
      </header>
      <nav class="profile-tabs" aria-label="Profile sections" role="tablist">
        <button class="is-active" type="button" role="tab" aria-selected="true" aria-controls="profile-posts-panel" data-profile-tab="posts">Posts</button>
        <button type="button" role="tab" aria-selected="false" aria-controls="profile-media-panel" data-profile-tab="media">Media</button>
        <button type="button" role="tab" aria-selected="false" aria-controls="profile-about-panel" data-profile-tab="about">About</button>
      </nav>
      <section class="profile-tab-panel" id="profile-posts-panel" role="tabpanel" data-profile-panel="posts">
        <div class="section-heading"><h2>Posts</h2></div>
        <div class="feed-list" data-profile-posts>${posts.length ? posts.map(postCardMarkup).join("") : '<p class="empty-state">No posts to show yet.</p>'}</div>
        <div class="pagination"><button class="button button-secondary" type="button" data-posts-more>Load more posts</button></div>
      </section>
      <section class="profile-tab-panel" id="profile-media-panel" role="tabpanel" data-profile-panel="media" hidden>
        ${isOwner ? `<form class="section-card profile-media-form" data-media-form>
          <h2>Add a profile photo</h2><label class="field"><span>Image</span><input type="file" name="image" accept="image/jpeg,image/png,image/webp" required></label>
          <label class="field"><span>Caption (optional)</span><input name="caption" maxlength="500"></label><button class="button button-secondary" type="submit">Add photo</button>
        </form>` : ""}
        <section class="section-card profile-gallery"><div class="section-heading"><h2>Media</h2></div><div class="profile-media-grid" data-profile-media>${media.length ? media.map(mediaCardMarkup).join("") : '<p class="muted">No profile photos have been shared yet.</p>'}</div><div class="pagination"><button class="button button-secondary" type="button" data-media-more>Load more photos</button></div></section>
      </section>
      <section class="profile-tab-panel" id="profile-about-panel" role="tabpanel" data-profile-panel="about" hidden>
        <section class="section-card profile-about"><div class="section-heading"><h2>About</h2>${isOwner ? '<button class="button button-secondary button-small" type="button" data-about-edit>Edit profile</button>' : ""}</div>
          <p class="profile-bio">${escapeHtml(data.bio || "No bio yet.")}</p>
          <p class="profile-joined">Joined <strong>${escapeHtml(formatDate(data.created_at))}</strong></p>
        </section>
      ${isOwner ? `<form class="section-card profile-edit-form" data-profile-form hidden>
        <h2>Edit your profile</h2>
        <label class="field"><span>First name</span><input name="first_name" maxlength="150" value="${escapeHtml(data.first_name || "")}"></label>
        <label class="field"><span>Last name</span><input name="last_name" maxlength="150" value="${escapeHtml(data.last_name || "")}"></label>
        <label class="field"><span>Bio</span><textarea name="bio" maxlength="500" rows="3">${escapeHtml(data.bio || "")}</textarea></label>
        <label class="field"><span>Profile photo</span><input type="file" name="avatar" accept="image/jpeg,image/png,image/webp"></label>
        <label class="field"><span>Cover photo</span><input type="file" name="cover_image" accept="image/jpeg,image/png,image/webp"></label>
        <p class="form-error" data-profile-error role="alert"></p>
        <div class="dialog-actions"><button class="button button-quiet" type="button" data-cancel-edit>Cancel</button><button class="button button-primary" type="submit">Save profile</button></div>
      </form>` : ""}
      </section>
    </section>`;

  bindPostActions(root, { onPostChanged: loadPosts });
  root.querySelectorAll("[data-profile-tab]").forEach((button) => {
    button.addEventListener("click", () => activateProfileTab(button.dataset.profileTab));
  });
  root.querySelector("[data-edit-profile]")?.addEventListener("click", () => {
    activateProfileTab("about");
    const form = root.querySelector("[data-profile-form]");
    form.hidden = false;
    form.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  root.querySelector("[data-cancel-edit]")?.addEventListener("click", () => {
    root.querySelector("[data-profile-form]").hidden = true;
  });
  root.querySelector("[data-profile-form]")?.addEventListener("submit", saveProfile);
  root.querySelector("[data-media-form]")?.addEventListener("submit", saveMedia);
  root.querySelector("[data-follow-user]")?.addEventListener("click", toggleFollow);
  root.querySelector("[data-media-more]")?.addEventListener("click", loadMoreMedia);
  root.querySelector("[data-posts-more]")?.addEventListener("click", loadMorePosts);
  root.querySelector("[data-about-edit]")?.addEventListener("click", () => {
    activateProfileTab("about");
    const form = root.querySelector("[data-profile-form]");
    form.hidden = false;
    form.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  root.querySelectorAll("[data-delete-media]").forEach((button) => {
    button.dataset.bound = "true";
    button.addEventListener("click", removeMedia);
  });
  const requestedTab = new URLSearchParams(window.location.search).get("tab");
  if (["posts", "media", "about"].includes(requestedTab)) {
    activateProfileTab(requestedTab);
  }
}

function activateProfileTab(tab) {
  root.querySelectorAll("[data-profile-tab]").forEach((button) => {
    const active = button.dataset.profileTab === tab;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  root.querySelectorAll("[data-profile-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.profilePanel !== tab;
  });
}

async function loadPosts() {
  const data = await getUserPosts(username);
  const posts = getResults(data);
  postPage = getNextPage(data);
  const count = root.querySelector("[data-profile-post-count]");
  if (count && Number.isFinite(data.count)) {
    count.textContent = data.count.toLocaleString();
  }
  root.querySelector("[data-profile-posts]").innerHTML = posts.length
    ? posts.map(postCardMarkup).join("")
    : '<p class="empty-state">No posts to show yet.</p>';
  root.querySelector("[data-posts-more]").hidden = !postPage;
}

async function loadMorePosts() {
  const button = root.querySelector("[data-posts-more]");
  if (!postPage) return;
  button.disabled = true;
  try {
    const data = await getUserPosts(username, postPage);
    root.querySelector("[data-profile-posts]").insertAdjacentHTML("beforeend", getResults(data).map(postCardMarkup).join(""));
    postPage = getNextPage(data);
    button.hidden = !postPage;
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function loadMoreMedia() {
  const button = root.querySelector("[data-media-more]");
  if (!mediaPage) return;
  button.disabled = true;
  try {
    const data = await getUserMedia(username, mediaPage);
    root.querySelector("[data-profile-media]").insertAdjacentHTML("beforeend", getResults(data).map(mediaCardMarkup).join(""));
    mediaPage = getNextPage(data);
    button.hidden = !mediaPage;
    root.querySelectorAll("[data-delete-media]:not([data-bound])").forEach((item) => {
      item.dataset.bound = "true";
      item.addEventListener("click", removeMedia);
    });
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function saveProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('[type="submit"]');
  const errorNode = form.querySelector("[data-profile-error]");
  const body = new FormData(form);
  for (const [name, value] of body.entries()) {
    if (value instanceof File && !value.size) body.delete(name);
  }
  submit.disabled = true;
  errorNode.textContent = "";
  try {
    await updateProfile(body);
    showToast("Profile updated.", "success");
    await loadProfile();
  } catch (error) {
    errorNode.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}

async function saveMedia(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  try {
    const values = new FormData(form);
    await addProfileMedia(username, values.get("image"), values.get("caption") || "");
    showToast("Photo added to your profile.", "success");
    await loadProfile();
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    submit.disabled = false;
  }
}

async function removeMedia(event) {
  const button = event.currentTarget;
  const confirmed = await confirmDialog({
    title: "Remove this photo?",
    description: "This image will be permanently deleted from your profile.",
    confirmLabel: "Remove photo",
    danger: true,
  });
  if (!confirmed) return;
  try {
    await deleteProfileMedia(button.dataset.deleteMedia);
    button.closest("[data-media-id]").remove();
    showToast("Photo removed.", "success");
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function toggleFollow(event) {
  const button = event.currentTarget;
  const following = button.dataset.following === "true";
  button.disabled = true;
  try {
    const result = await (following ? unfollowUser(username) : followUser(username));
    button.dataset.following = String(result.following);
    button.textContent = result.following ? "Following" : "Follow";
    const count = root.querySelector("[data-follower-count]");
    if (count && Number.isFinite(result.follower_count)) count.textContent = result.follower_count.toLocaleString();
    showToast(result.following ? `You’re now following @${username}.` : `You unfollowed @${username}.`, "success");
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function isFollowingProfile() {
  let page = 1;
  while (page) {
    const data = await getFollowers(user.username, "following", page);
    if (getResults(data).some((item) => item.username === username)) return true;
    page = getNextPage(data);
  }
  return false;
}

async function loadProfile() {
  root.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Loading profile…</div>';
  try {
    const data = isOwner ? await getMyProfile() : await getUserProfile(username);
    const [mediaData, postsData] = await Promise.all([
      getUserMedia(username),
      getUserPosts(username),
    ]);
    const media = getResults(mediaData);
    mediaPage = getNextPage(mediaData);
    const posts = getResults(postsData);
    postPage = getNextPage(postsData);
    profileMarkup(data, media, posts, data.post_count);
    root.querySelector("[data-media-more]").hidden = !mediaPage;
    root.querySelector("[data-posts-more]").hidden = !postPage;

    if (!isOwner) {
      const followButton = root.querySelector("[data-follow-user]");
      try {
        const following = await isFollowingProfile();
        followButton.dataset.following = String(following);
        followButton.textContent = following ? "Following" : "Follow";
      } catch (error) {
        followButton.disabled = true;
        followButton.textContent = "Follow status unavailable";
        followButton.title = "Reload this profile to retry loading follow status.";
        showToast(`Could not load follow status: ${error.message}`, "error");
      }
    }
  } catch (error) {
    root.innerHTML = `<div class="inline-error">${escapeHtml(error.message)} <button class="text-button" type="button" data-profile-retry>Try again</button></div>`;
    root.querySelector("[data-profile-retry]")?.addEventListener("click", loadProfile);
  }
}

await loadProfile();