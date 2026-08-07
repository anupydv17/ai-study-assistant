/**
 * Page script for login.html.
 */

import { ApiError, isLoggedIn, login } from "./api.js";
import { hideMessage, setBusy, showMessage } from "./ui.js";

if (isLoggedIn()) {
  window.location.replace("dashboard.html");
}

const form = document.getElementById("login-form");
const submitButton = document.getElementById("submit-button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  const email = form.email.value.trim();
  const password = form.password.value;

  if (!email || !password) {
    showMessage("Please enter your email and password.");
    return;
  }

  setBusy(submitButton, true, "Logging in…");

  try {
    await login({ email, password });
    window.location.replace("dashboard.html");
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      // Same vague wording the backend uses, for the same reason: never
      // reveal whether an email is registered.
      showMessage("Incorrect email or password.");
    } else if (error instanceof ApiError) {
      showMessage(error.message);
    } else {
      showMessage("Something went wrong. Please try again.");
      console.error(error);
    }

    setBusy(submitButton, false);
  }
});
