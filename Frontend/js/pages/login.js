import { initShell } from "../app.js";
import { signIn } from "../services/auth-service.js";
import { showToast } from "../components/toast.js";
import { installPasswordToggles } from "../components/password-toggle.js";

const user = await initShell();
const form = document.querySelector("#login-form");
const message = document.querySelector("#form-message");

installPasswordToggles();

if (user) window.location.replace("feed.html");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = "Please wait…";
  try {
    const values = new FormData(form);
    await signIn(
      values.get("identifier"),
      values.get("password"),
      values.get("remember") === "on",
    );
    showToast("You’re signed in. Welcome back!", "success");
    const candidate = new URLSearchParams(window.location.search).get("next");
    const destination = candidate ? new URL(candidate, window.location.href) : null;
    const allowed = destination
      && destination.origin === window.location.origin
      && /\/pages\/(feed|profile|search|notifications|admin)\.html$/.test(destination.pathname);
    window.location.assign(allowed ? destination.href : "feed.html");
  } catch (error) {
    message.textContent = error.message || "We couldn’t log you in. Check your details and try again.";
  } finally {
    button.disabled = false;
    button.textContent = "Sign in";
  }
});