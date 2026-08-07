/**
 * Page script for register.html.
 */

import { ApiError, isLoggedIn, login, register } from "./api.js";
import { hideMessage, setBusy, showMessage } from "./ui.js";

// Already logged in? No reason to be on this page.
if (isLoggedIn()) {
  window.location.replace("dashboard.html");
}

const form = document.getElementById("register-form");
const submitButton = document.getElementById("submit-button");

form.addEventListener("submit", async (event) => {
  // Stop the browser's default behaviour: reloading the page and sending the
  // form the old-fashioned way. We want to stay put and use fetch().
  event.preventDefault();
  hideMessage();

  const fullName = form.full_name.value.trim();
  const email = form.email.value.trim();
  const password = form.password.value;

  // A quick check so obvious mistakes do not need a network round trip.
  // The backend re-checks everything; this is convenience, not security.
  if (!fullName || !email || !password) {
    showMessage("Please fill in every field.");
    return;
  }

  setBusy(submitButton, true, "Creating account…");

  try {
    await register({ email, fullName, password });

    // Log the new user straight in rather than making them type it again.
    await login({ email, password });

    window.location.replace("dashboard.html");
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      showMessage("That email is already registered. Try logging in instead.");
    } else if (error instanceof ApiError) {
      showMessage(error.message);
    } else {
      showMessage("Something went wrong. Please try again.");
      console.error(error);
    }

    setBusy(submitButton, false);
  }
});
