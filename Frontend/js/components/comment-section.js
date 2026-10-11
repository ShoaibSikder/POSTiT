import { addComment, deleteComment, getComments } from "../api/comments-api.js";
import { getNextPage, getResults } from "../api/api-client.js";
import { getCachedUser } from "../services/auth-service.js";
import {
  avatarMarkup,
  escapeHtml,
  timeAgo,
} from "../utils/formatters.js";
import { confirmDialog, openTextDialog } from "./modal.js";
import { showToast } from "./toast.js";

function commentMarkup(comment) {
  const user = getCachedUser();
  const canDelete = user?.username === comment.author;
  return `<div class="comment-item" data-comment-id="${comment.id}">
    ${avatarMarkup({ username: comment.author, avatar: comment.author_avatar }, "avatar-small")}
    <div class="comment-bubble"><strong>${escapeHtml(comment.author)}</strong><p>${escapeHtml(comment.content)}</p><small class="muted">${escapeHtml(timeAgo(comment.created_at))}</small></div>
    ${canDelete ? `<button class="icon-button" type="button" data-comment-actions="${comment.id}" aria-label="Comment actions">···</button>` : ""}
  </div>`;
}

export async function mountComments(panel, postId) {
  panel.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Loading comments</div>';
  try {
    const data = await getComments(postId);
    const comments = getResults(data);
    const user = getCachedUser();
    panel.innerHTML = `
      <div class="comment-list">${comments.length ? comments.map(commentMarkup).join("") : '<p class="muted small-copy">No comments yet. Start a kind conversation.</p>'}</div>
      ${user ? `<form class="comment-compose" data-comment-form><label class="sr-only" for="comment-${postId}">Write a comment</label><input id="comment-${postId}" name="content" maxlength="1000" placeholder="Add a thoughtful comment…" required><button class="button button-primary" type="submit">Send</button></form>` : `<p class="muted small-copy"><a class="text-link" href="../pages/login.html">Log in</a> to join the conversation.</p>`}
      ${data?.next ? '<button class="text-button" type="button" data-comments-more>Load more comments</button>' : ""}`;

    let nextPage = getNextPage(data);
    panel.querySelector("[data-comment-form]")?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const input = form.elements.content;
      const button = form.querySelector("button");
      button.disabled = true;
      try {
        await addComment(postId, input.value.trim());
        await mountComments(panel, postId);
        showToast("Your comment was added.", "success");
      } catch (error) {
        showToast(error.message, "error");
        button.disabled = false;
      }
    });
    panel.querySelector("[data-comments-more]")?.addEventListener("click", async (event) => {
      if (!nextPage) return;
      try {
        const more = await getComments(postId, nextPage);
        panel.querySelector(".comment-list").insertAdjacentHTML(
          "beforeend",
          getResults(more).map(commentMarkup).join(""),
        );
        nextPage = getNextPage(more);
        if (!nextPage) event.currentTarget.remove();
      } catch (error) {
        showToast(error.message, "error");
      }
    });
    if (panel.dataset.commentActionsReady) return;
    panel.dataset.commentActionsReady = "true";
    panel.addEventListener("click", async (event) => {
      const action = event.target.closest("[data-comment-actions]");
      if (!action) return;
      const comment = action.closest("[data-comment-id]");
      const commentId = action.dataset.commentActions;
      const confirmed = await confirmDialog({
        title: "Remove this comment?",
        description: "This comment will be permanently removed.",
        confirmLabel: "Remove comment",
        danger: true,
      });
      if (!confirmed) return;
      try {
        await deleteComment(commentId);
        comment.remove();
        showToast("Comment removed.", "success");
      } catch (error) {
        showToast(error.message, "error");
      }
    });
    return true;
  } catch (error) {
    panel.innerHTML = `<div class="inline-error">${escapeHtml(error.message)} <button class="text-button" type="button" data-retry-comments>Try again</button></div>`;
    panel.querySelector("[data-retry-comments]")?.addEventListener("click", () => mountComments(panel, postId));
    return false;
  }
}
