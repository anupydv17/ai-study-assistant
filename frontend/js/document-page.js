/**
 * Page script for document.html.
 *
 * Loads the document, wires up the tabs, and hands each tab to its own
 * feature module. The same principle as the backend: one file, one job.
 */

import { ApiError, getDocument, isLoggedIn, logout } from "./api.js";
import { initChat } from "./features/chat.js";
import { initFlashcards } from "./features/flashcards.js";
import { initQuiz } from "./features/quiz.js";
import { initSummary } from "./features/summary.js";
import { formatDate, formatFileSize, formatPages } from "./format.js";
import { showMessage } from "./ui.js";

if (!isLoggedIn()) {
  window.location.replace("login.html");
}

const documentId = new URLSearchParams(window.location.search).get("id");

if (!documentId) {
  window.location.replace("dashboard.html");
}

/** Send an expired session back to the login page. Returns true if handled. */
function handleAuthError(error) {
  if (error instanceof ApiError && error.status === 401) {
    logout();
    window.location.replace("login.html");
    return true;
  }
  return false;
}

document.getElementById("logout-button").addEventListener("click", () => {
  logout();
  window.location.replace("login.html");
});

/* ------------------------------------------------------------------ */
/* Tabs                                                                */
/* ------------------------------------------------------------------ */

const chat = initChat(documentId, handleAuthError);
let chatLoaded = false;

function showTab(name) {
  for (const tab of document.querySelectorAll(".tab")) {
    tab.classList.toggle("is-active", tab.dataset.tab === name);
  }

  for (const panel of document.querySelectorAll(".tab-panel")) {
    panel.hidden = panel.dataset.panel !== name;
  }

  // Load the conversation the first time the chat tab is opened, not on page
  // load — most visits never touch it.
  if (name === "chat" && !chatLoaded) {
    chatLoaded = true;
    chat.loadHistory();
  }
}

for (const tab of document.querySelectorAll(".tab")) {
  tab.addEventListener("click", () => showTab(tab.dataset.tab));
}

/* ------------------------------------------------------------------ */
/* Document header                                                     */
/* ------------------------------------------------------------------ */

async function loadDocument() {
  try {
    const doc = await getDocument(documentId);

    document.title = `${doc.original_filename} — AI Study Assistant`;
    document.getElementById("document-title").textContent = doc.original_filename;
    document.getElementById("document-meta").textContent = [
      formatPages(doc.page_count),
      formatFileSize(doc.file_size_bytes),
      `uploaded ${formatDate(doc.created_at)}`,
    ].join(" · ");
  } catch (error) {
    if (handleAuthError(error)) return;

    document.getElementById("document-title").textContent = "Not found";
    showMessage("That document does not exist, or is not yours.");
  }
}

/* ------------------------------------------------------------------ */
/* Start                                                               */
/* ------------------------------------------------------------------ */

initSummary(documentId, handleAuthError);
initQuiz(documentId, handleAuthError);
initFlashcards(documentId, handleAuthError);

loadDocument();
