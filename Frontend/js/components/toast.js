import { escapeHtml } from "../utils/formatters.js";

let container;

export function showToast(message, type = "info") {
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-region";
    container.setAttribute("aria-live", "polite");
    container.setAttribute("aria-atomic", "false");
    document.body.append(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span class="toast-dot" aria-hidden="true"></span><p>${escapeHtml(message)}</p><button class="icon-button toast-dismiss" type="button" aria-label="Dismiss notification">×</button>`;
  container.append(toast);
  const dismiss = () => toast.remove();
  toast.querySelector(".toast-dismiss").addEventListener("click", dismiss);
  window.setTimeout(dismiss, 5200);
}