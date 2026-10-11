export function installPasswordToggles(root = document) {
  root.querySelectorAll("[data-toggle-password]").forEach((button) => {
    const input = button.closest(".password-control")?.querySelector("input");
    if (!input) {
      throw new Error("Password visibility button is missing its input.");
    }

    button.addEventListener("click", () => {
      const visible = input.type === "password";
      input.type = visible ? "text" : "password";
      button.textContent = visible ? "Hide" : "Show";
      button.setAttribute("aria-pressed", String(visible));
      button.setAttribute(
        "aria-label",
        `${visible ? "Hide" : "Show"} password`,
      );
    });
  });
}
