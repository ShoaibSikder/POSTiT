import { escapeHtml } from "../utils/formatters.js";

export function openTextDialog({
  title,
  description = "",
  initialValue = "",
  placeholder = "",
  submitLabel = "Save",
  required = true,
  maxLength = 500,
}) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "app-dialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card" data-dialog-form>
        <button class="icon-button dialog-close" type="button" data-dialog-cancel aria-label="Close dialog">×</button>
        <span class="eyebrow">POSTiT</span>
        <h2>${escapeHtml(title)}</h2>
        ${description ? `<p class="muted">${escapeHtml(description)}</p>` : ""}
        <label class="field-label" for="dialog-value">Your message</label>
        <textarea id="dialog-value" name="value" rows="4" maxlength="${maxLength}" placeholder="${escapeHtml(placeholder)}" ${required ? "required" : ""}>${escapeHtml(initialValue)}</textarea>
        <div class="dialog-actions">
          <button class="button button-quiet" type="button" data-dialog-cancel>Cancel</button>
          <button class="button button-primary" type="submit">${escapeHtml(submitLabel)}</button>
        </div>
      </form>`;
    document.body.append(dialog);
    const cleanup = (value) => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };
    dialog.querySelectorAll("[data-dialog-cancel]").forEach((button) => {
      button.addEventListener("click", () => cleanup(null));
    });
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      cleanup(null);
    });
    dialog.querySelector("[data-dialog-form]").addEventListener("submit", (event) => {
      event.preventDefault();
      cleanup(dialog.querySelector("textarea").value.trim());
    });
    dialog.showModal();
    dialog.querySelector("textarea").focus();
  });
}

export function confirmDialog({
  title,
  description,
  confirmLabel = "Continue",
  danger = false,
}) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "app-dialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card">
        <button class="icon-button dialog-close" type="button" data-cancel aria-label="Close dialog">×</button>
        <span class="eyebrow">PLEASE CONFIRM</span>
        <h2>${escapeHtml(title)}</h2>
        <p class="muted">${escapeHtml(description)}</p>
        <div class="dialog-actions">
          <button class="button button-quiet" type="button" data-cancel>Cancel</button>
          <button class="button ${danger ? "button-danger" : "button-primary"}" type="submit">${escapeHtml(confirmLabel)}</button>
        </div>
      </form>`;
    document.body.append(dialog);
    const cleanup = (value) => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };
    dialog.querySelectorAll("[data-cancel]").forEach((button) => {
      button.addEventListener("click", () => cleanup(false));
    });
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      cleanup(false);
    });
    dialog.querySelector("form").addEventListener("submit", (event) => {
      event.preventDefault();
      cleanup(true);
    });
    dialog.showModal();
  });
}