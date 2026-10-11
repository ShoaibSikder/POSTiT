import { initShell } from "../app.js";
import { signUp } from "../services/auth-service.js";
import { showToast } from "../components/toast.js";
import {
  validatePasswordMatch,
  validateRequired,
} from "../utils/validators.js";
import { installPasswordToggles } from "../components/password-toggle.js";

const user = await initShell();
const form = document.querySelector("#register-form");
const message = document.querySelector("#form-message");

installPasswordToggles();

if (user) window.location.replace("feed.html");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";
  const values = new FormData(form);
  const username = String(values.get("username") || "").trim();
  const email = String(values.get("email") || "").trim();
  const password = String(values.get("password") || "");
  const confirmation = String(values.get("password_confirmation") || "");
  const localErrors = [
    validateRequired(username, "Username"),
    validateRequired(email, "Email"),
    validateRequired(password, "Password"),
    password.length >= 8 ? "" : "Password must contain at least 8 characters.",
    validatePasswordMatch(password, confirmation),
  ].filter(Boolean);
  if (localErrors.length) {
    message.textContent = localErrors.join(" ");
    return;
  }

  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = "Please wait…";
  try {
    await signUp({
      username,
      email,
      password,
      password_confirmation: confirmation,
    });
    showToast("Your account is ready. Welcome to POSTiT!", "success");
    window.location.assign("feed.html");
  } catch (error) {
    message.textContent = error.message || "We couldn’t create your account. Please try again.";
  } finally {
    button.disabled = false;
    button.textContent = "Create account";
  }
});