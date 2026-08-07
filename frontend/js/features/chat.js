/**
 * The Chat tab.
 *
 * Loads past messages, sends new questions, and shows the question
 * immediately rather than waiting for the answer.
 */

import { ApiError, askQuestion, clearChat, getChatHistory } from "../api.js";
import { setBusy } from "../ui.js";

/** Build one message bubble. */
function buildMessage(role, content) {
  const wrapper = document.createElement("div");
  wrapper.className = `chat-message chat-${role}`;

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  bubble.textContent = content;

  wrapper.append(bubble);
  return wrapper;
}

/** A "thinking" bubble shown while we wait for the AI. */
function buildPending() {
  const wrapper = document.createElement("div");
  wrapper.className = "chat-message chat-assistant";

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble chat-pending";

  for (let i = 0; i < 3; i += 1) {
    const dot = document.createElement("span");
    dot.className = "dot";
    bubble.append(dot);
  }

  wrapper.append(bubble);
  return wrapper;
}

export function initChat(documentId, onAuthError) {
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendButton = document.getElementById("chat-button");
  const clearButton = document.getElementById("clear-chat-button");

  /** Keep the newest message in view. */
  function scrollToBottom() {
    log.scrollTop = log.scrollHeight;
  }

  function showEmptyState() {
    log.replaceChildren();
    const hint = document.createElement("p");
    hint.className = "panel-hint";
    hint.textContent = "Ask anything about these notes.";
    log.append(hint);
  }

  async function loadHistory() {
    try {
      const messages = await getChatHistory(documentId);

      if (messages.length === 0) {
        showEmptyState();
        return;
      }

      log.replaceChildren();
      for (const message of messages) {
        log.append(buildMessage(message.role, message.content));
      }
      scrollToBottom();
    } catch (error) {
      if (onAuthError(error)) return;
      console.error(error);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = input.value.trim();
    if (!question) return;

    // Clear the empty-state hint the first time a message is sent.
    if (log.querySelector(".panel-hint")) {
      log.replaceChildren();
    }

    // Optimistic UI: show the question straight away. Waiting 10 seconds to
    // see your own typing makes the app feel frozen.
    log.append(buildMessage("user", question));
    input.value = "";

    const pending = buildPending();
    log.append(pending);
    scrollToBottom();

    setBusy(sendButton, true, "…");
    input.disabled = true;

    try {
      const result = await askQuestion(documentId, question);
      pending.replaceWith(buildMessage("assistant", result.answer.content));
    } catch (error) {
      if (onAuthError(error)) return;

      pending.remove();

      const failure = document.createElement("p");
      failure.className = "message error";
      failure.textContent =
        error instanceof ApiError ? error.message : "Could not send that message.";
      log.append(failure);

      // Give the question back so the user does not have to retype it.
      input.value = question;
    } finally {
      setBusy(sendButton, false);
      input.disabled = false;
      input.focus();
      scrollToBottom();
    }
  });

  clearButton.addEventListener("click", async () => {
    if (!window.confirm("Delete this conversation?")) return;

    try {
      await clearChat(documentId);
      showEmptyState();
    } catch (error) {
      if (onAuthError(error)) return;
      console.error(error);
    }
  });

  return { loadHistory };
}
