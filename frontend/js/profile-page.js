/**
 * Page script for profile.html.
 */

import {
  ApiError,
  changePassword,
  deleteAccount,
  getCurrentUser,
  isLoggedIn,
  logout,
  updateProfile,
} from "./api.js";
import { formatDate } from "./format.js";
import { hideMessage, setBusy, showMessage } from "./ui.js";

if (!isLoggedIn()) {
  window.location.replace("login.html");
}

const profileForm = document.getElementById("profile-form");
const profileButton = document.getElementById("profile-button");
const passwordForm = document.getElementById("password-form");
const passwordButton = document.getElementById("password-button");

function goToLogin() {
  logout();
  window.location.replace("login.html");
}

function handleAuthError(error) {
  if (error instanceof ApiError && error.status === 401) {
    goToLogin();
    return true;
  }
  return false;
}

document.getElementById("logout-button").addEventListener("click", goToLogin);

/* ------------------------------------------------------------------ */
/* Load                                                                */
/* ------------------------------------------------------------------ */

async function loadProfile() {
  try {
    const user = await getCurrentUser();

    document.getElementById("full_name").value = user.full_name;
    document.getElementById("email").value = user.email;
    document.getElementById("member-since").textContent = formatDate(
      user.created_at
    );
  } catch (error) {
    if (handleAuthError(error)) return;
    showMessage("Could not load your profile.");
    console.error(error);
  }
}

/* ------------------------------------------------------------------ */
/* Update name                                                         */
/* ------------------------------------------------------------------ */

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  const fullName = document.getElementById("full_name").value.trim();
  if (!fullName) {
    showMessage("Your name cannot be empty.");
    return;
  }

  setBusy(profileButton, true, "Saving…");

  try {
    await updateProfile(fullName);
    showMessage("Profile updated.", "success");
  } catch (error) {
    if (handleAuthError(error)) return;
    showMessage(
      error instanceof ApiError ? error.message : "Could not save your changes."
    );
  } finally {
    setBusy(profileButton, false);
  }
});

/* ------------------------------------------------------------------ */
/* Change password                                                     */
/* ------------------------------------------------------------------ */

passwordForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  const current = document.getElementById("current_password").value;
  const next = document.getElementById("new_password").value;
  const confirmation = document.getElementById("confirm_password").value;

  // The "confirm" field exists only in the browser — the API never sees it.
  // Its whole job is catching typos before they lock someone out.
  if (next !== confirmation) {
    showMessage("The two new passwords do not match.");
    return;
  }

  if (next.length < 8) {
    showMessage("Your new password must be at least 8 characters.");
    return;
  }

  setBusy(passwordButton, true, "Changing…");

  try {
    await changePassword(current, next);

    // The password change invalidated this very token, so every following
    // request would fail. Send the user to log in again with the new one.
    window.alert("Password changed. Please log in again with your new password.");
    goToLogin();
  } catch (error) {
    if (handleAuthError(error)) return;
    showMessage(
      error instanceof ApiError ? error.message : "Could not change your password."
    );
    setBusy(passwordButton, false);
  }
});

/* ------------------------------------------------------------------ */
/* Delete account                                                      */
/* ------------------------------------------------------------------ */

document
  .getElementById("delete-account-button")
  .addEventListener("click", async () => {
    // Typing the word is deliberate friction. A single "Are you sure?" is too
    // easy to click through for something irreversible.
    const typed = window.prompt(
      'This deletes everything, permanently.\n\nType DELETE to confirm:'
    );

    if (typed !== "DELETE") {
      return;
    }

    try {
      await deleteAccount();
      window.alert("Your account has been deleted.");
      goToLogin();
    } catch (error) {
      if (handleAuthError(error)) return;
      showMessage("Could not delete your account.");
      console.error(error);
    }
  });

loadProfile();
