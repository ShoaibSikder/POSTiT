import { getCachedUser } from "../services/auth-service.js";
import {
  avatarMarkup,
  escapeHtml,
  mediaUrl,
  timeAgo,
} from "../utils/formatters.js";
import { icon } from "./icons.js";

function postImages(images = []) {
  if (!images.length) return "";
  return `<div class="post-gallery post-gallery-${Math.min(images.length, 3)}">${images
    .slice(0, 4)
    .map(
      (image) =>
        `<a class="post-image-link" href="${escapeHtml(mediaUrl(image.image))}" target="_blank" rel="noopener noreferrer"><img src="${escapeHtml(mediaUrl(image.image))}" alt="Photo shared in this post" loading="lazy"></a>`,
    )
    .join("")}</div>`;
}

export function postCardMarkup(post) {
  const user = getCachedUser();
  const isOwner = user?.username === post.author;
  return `
    <article class="post-card" data-post-id="${post.id}">
      <div class="post-card-header">
        <a class="post-author" href="../pages/profile.html?u=${encodeURIComponent(post.author)}">
          ${avatarMarkup({ username: post.author, avatar: post.author_avatar }, "avatar-small")}
          <span><strong>${escapeHtml(post.author)}</strong><small>${escapeHtml(timeAgo(post.created_at))}</small></span>
        </a>
        <div class="post-menu">
          ${isOwner ? `<button class="icon-button post-more" type="button" data-post-menu="${post.id}" aria-label="Post actions">${icon("more")}</button><div class="post-menu-popover" data-menu-for="${post.id}" hidden><button type="button" data-post-edit="${post.id}">Edit post</button><button type="button" class="text-danger" data-post-delete="${post.id}">Delete post</button></div>` : ""}
        </div>
      </div>
      ${post.content ? `<p class="post-content">${escapeHtml(post.content).replace(/\n/g, "<br>")}</p>` : ""}
      ${postImages(post.images)}
      <div class="post-stats"><span>${Number(post.likes_count || 0).toLocaleString()} appreciations</span><span>${Number(post.comments_count || 0).toLocaleString()} comments</span></div>
      <div class="post-actions">
        <button class="post-action ${post.liked_by_user ? "is-liked" : ""}" type="button" data-post-like="${post.id}" aria-pressed="${Boolean(post.liked_by_user)}">${icon("heart")}<span>${post.liked_by_user ? "Appreciated" : "Appreciate"}</span></button>
        <button class="post-action" type="button" data-comments-toggle="${post.id}">${icon("message")}<span>Comment</span></button>
        <button class="post-action post-share" type="button" data-post-share="${post.id}" data-post-author="${escapeHtml(post.author)}">${icon("share")}<span>Share</span></button>
      </div>
      <section class="comment-panel" data-comment-panel="${post.id}" hidden></section>
    </article>`;
}