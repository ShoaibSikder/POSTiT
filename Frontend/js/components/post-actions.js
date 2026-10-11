import { deletePost, likePost, unlikePost, updatePost } from "../api/posts-api.js";
import { getCachedUser } from "../services/auth-service.js";
import { confirmDialog, openTextDialog } from "./modal.js";
import { mountComments } from "./comment-section.js";
import { showToast } from "./toast.js";

export function bindPostActions(root, { onPostChanged = () => {} } = {}) {
  if (root.dataset.postActionsReady) return;
  root.dataset.postActionsReady = "true";
  root.addEventListener("click", async (event) => {
    const likeButton = event.target.closest("[data-post-like]");
    const commentsButton = event.target.closest("[data-comments-toggle]");
    const menuButton = event.target.closest("[data-post-menu]");
    const editButton = event.target.closest("[data-post-edit]");
    const deleteButton = event.target.closest("[data-post-delete]");
    const shareButton = event.target.closest("[data-post-share]");

    if (likeButton) {
      if (!getCachedUser()) {
        showToast("Log in to appreciate a post.", "info");
        return;
      }
      likeButton.disabled = true;
      const postId = likeButton.dataset.postLike;
      const wasLiked = likeButton.getAttribute("aria-pressed") === "true";
      try {
        await (wasLiked ? unlikePost(postId) : likePost(postId));
        const card = likeButton.closest("[data-post-id]");
        const stats = card.querySelector(".post-stats span");
        const previous = Number(stats.textContent.match(/[\d,]+/)?.[0].replaceAll(",", "") || 0);
        stats.textContent = `${Math.max(0, previous + (wasLiked ? -1 : 1)).toLocaleString()} appreciations`;
        likeButton.classList.toggle("is-liked", !wasLiked);
        likeButton.setAttribute("aria-pressed", String(!wasLiked));
        likeButton.querySelector("span").textContent = wasLiked ? "Appreciate" : "Appreciated";
      } catch (error) {
        showToast(error.message, "error");
      } finally {
        likeButton.disabled = false;
      }
    }

    if (commentsButton) {
      const panel = root.querySelector(
        `[data-comment-panel="${commentsButton.dataset.commentsToggle}"]`,
      );
      panel.hidden = !panel.hidden;
      if (!panel.hidden && !panel.dataset.loaded) {
        const loaded = await mountComments(panel, commentsButton.dataset.commentsToggle);
        if (loaded) panel.dataset.loaded = "true";
      }
    }

    if (menuButton) {
      const menu = root.querySelector(`[data-menu-for="${menuButton.dataset.postMenu}"]`);
      menu.hidden = !menu.hidden;
    }

    if (editButton) {
      const card = editButton.closest("[data-post-id]");
      const current = card.querySelector(".post-content")?.textContent || "";
      const next = await openTextDialog({
        title: "Edit your moment",
        description: "Update the words on your post. Photos can’t be changed in this editor.",
        initialValue: current,
        placeholder: "Share a thought…",
        submitLabel: "Save changes",
        maxLength: 2000,
      });
      if (next === null) return;
      try {
        await updatePost(editButton.dataset.postEdit, next);
        showToast("Your post has been updated.", "success");
        await onPostChanged();
      } catch (error) {
        showToast(error.message, "error");
      }
    }

    if (deleteButton) {
      const confirmed = await confirmDialog({
        title: "Delete this post?",
        description: "This post and its attached photos will be permanently removed.",
        confirmLabel: "Delete post",
        danger: true,
      });
      if (!confirmed) return;
      try {
        await deletePost(deleteButton.dataset.postDelete);
        showToast("Post deleted.", "success");
        await onPostChanged();
      } catch (error) {
        showToast(error.message, "error");
      }
    }

    if (shareButton) {
      const card = shareButton.closest("[data-post-id]");
      const text = `${shareButton.dataset.postAuthor} on POSTiT: ${card.querySelector(".post-content")?.textContent || "A photo post"}`;
      if (!navigator.clipboard?.writeText) {
        showToast("Copying to clipboard is not supported by this browser.", "error");
        return;
      }
      try {
        await navigator.clipboard.writeText(text);
        showToast("Post text copied. Direct post links aren’t available yet.", "success");
      } catch {
        showToast("Clipboard access was denied by your browser.", "error");
      }
    }
  });
}
