/**
 * Page script for dashboard.html.
 *
 * Loads the user's documents, handles uploads, and handles deletion.
 */

import {
  ApiError,
  deleteDocument,
  getCurrentUser,
  isLoggedIn,
  listDocuments,
  logout,
  uploadDocument,
} from "./api.js";
import { formatDate, formatFileSize, formatPages } from "./format.js";
import { hideMessage, setBusy, showMessage } from "./ui.js";

if (!isLoggedIn()) {
  window.location.replace("login.html");
}

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // must match MAX_UPLOAD_SIZE_MB

const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadButton = document.getElementById("upload-button");
const listElement = document.getElementById("document-list");
const loadingElement = document.getElementById("documents-loading");
const emptyElement = document.getElementById("documents-empty");
const countElement = document.getElementById("document-count");

/* ------------------------------------------------------------------ */
/* Session                                                             */
/* ------------------------------------------------------------------ */

document.getElementById("logout-button").addEventListener("click", () => {
  logout();
  window.location.replace("login.html");
});

/** Send an expired or invalid session back to the login page. */
function handleAuthError(error) {
  if (error instanceof ApiError && error.status === 401) {
    logout();
    window.location.replace("login.html");
    return true;
  }
  return false;
}

async function loadUser() {
  try {
    const user = await getCurrentUser();
    document.getElementById("user-name").textContent = user.full_name;
  } catch (error) {
    handleAuthError(error);
  }
}

/* ------------------------------------------------------------------ */
/* Rendering                                                           */
/* ------------------------------------------------------------------ */

/**
 * Build one row of the document list.
 *
 * Every user-supplied value goes in through textContent, never innerHTML, so
 * a filename containing HTML is displayed rather than executed.
 */
function buildDocumentRow(document_) {
  const item = document.createElement("li");
  item.className = "document-item";

  const info = document.createElement("div");
  info.className = "document-info";

  const name = document.createElement("p");
  name.className = "document-name";
  name.textContent = document_.original_filename;

  const meta = document.createElement("p");
  meta.className = "document-meta";
  meta.textContent = [
    formatPages(document_.page_count),
    formatFileSize(document_.file_size_bytes),
    formatDate(document_.created_at),
  ].join(" · ");

  info.append(name, meta);

  const actions = document.createElement("div");
  actions.className = "document-actions";

  if (document_.has_text) {
    const studyLink = document.createElement("a");
    studyLink.className = "button-link";
    studyLink.href = `document.html?id=${document_.id}`;
    studyLink.textContent = "Study";
    actions.append(studyLink);
  } else {
    // A scanned PDF. Say why the button is missing instead of showing a
    // button that would only fail.
    const warning = document.createElement("span");
    warning.className = "tag tag-warning";
    warning.textContent = "No readable text";
    actions.append(warning);
  }

  const deleteButton = document.createElement("button");
  deleteButton.className = "button-danger";
  deleteButton.type = "button";
  deleteButton.textContent = "Delete";
  deleteButton.addEventListener("click", () => removeDocument(document_, item));
  actions.append(deleteButton);

  item.append(info, actions);
  return item;
}

/** Show exactly one of: loading, empty state, or the list. */
function renderDocuments(documents) {
  loadingElement.hidden = true;
  listElement.replaceChildren();

  countElement.textContent =
    documents.length === 1 ? "1 document" : `${documents.length} documents`;

  if (documents.length === 0) {
    emptyElement.hidden = false;
    listElement.hidden = true;
    return;
  }

  emptyElement.hidden = true;
  listElement.hidden = false;

  for (const document_ of documents) {
    listElement.append(buildDocumentRow(document_));
  }
}

/* ------------------------------------------------------------------ */
/* Actions                                                             */
/* ------------------------------------------------------------------ */

async function loadDocuments() {
  try {
    renderDocuments(await listDocuments());
  } catch (error) {
    if (handleAuthError(error)) return;
    loadingElement.hidden = true;
    showMessage("Could not load your documents. Is the backend running?");
    console.error(error);
  }
}

async function removeDocument(document_, rowElement) {
  const confirmed = window.confirm(
    `Delete "${document_.original_filename}"?\n\n` +
      "Its summaries, quizzes, flashcards and chat history will be deleted too."
  );
  if (!confirmed) return;

  try {
    await deleteDocument(document_.id);
    rowElement.remove();
    // Re-fetch so the count and empty state stay correct.
    await loadDocuments();
  } catch (error) {
    if (handleAuthError(error)) return;
    showMessage("Could not delete that document.");
    console.error(error);
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  const file = fileInput.files[0];
  if (!file) {
    showMessage("Choose a PDF first.");
    return;
  }

  // Client-side checks are for fast feedback only. The backend re-validates
  // both of these, and the backend is the one that matters.
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showMessage("That does not look like a PDF.");
    return;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    showMessage(`"${file.name}" is larger than the 10 MB limit.`);
    return;
  }

  setBusy(uploadButton, true, "Uploading…");

  try {
    await uploadDocument(file);
    uploadForm.reset();
    showMessage(`"${file.name}" uploaded.`, "success");
    await loadDocuments();
  } catch (error) {
    if (handleAuthError(error)) return;
    showMessage(
      error instanceof ApiError ? error.message : "Upload failed. Try again."
    );
    console.error(error);
  } finally {
    // `finally` runs whether the upload worked or not, so the button can
    // never get stuck saying "Uploading…".
    setBusy(uploadButton, false);
  }
});

/* ------------------------------------------------------------------ */
/* Start                                                               */
/* ------------------------------------------------------------------ */

loadUser();
loadDocuments();
