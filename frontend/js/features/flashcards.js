/**
 * The Flashcards tab.
 *
 * Each card shows its front, and flips to the back when clicked.
 */

import { ApiError, generateFlashcards } from "../api.js";
import { setBusy } from "../ui.js";
import { renderError, renderLoading } from "./shared.js";

function buildCard(card) {
  // A button, not a div: it is clickable, so it should be keyboard-reachable
  // and announced as interactive by screen readers.
  const element = document.createElement("button");
  element.className = "flashcard";
  element.type = "button";
  element.setAttribute("aria-pressed", "false");

  const front = document.createElement("p");
  front.className = "flashcard-face";
  front.textContent = card.front;

  const back = document.createElement("p");
  back.className = "flashcard-face flashcard-back";
  back.textContent = card.back;
  back.hidden = true;

  const hint = document.createElement("span");
  hint.className = "flashcard-hint";
  hint.textContent = "Click to reveal";

  element.append(front, back, hint);

  element.addEventListener("click", () => {
    const showingBack = !back.hidden;
    front.hidden = !showingBack;
    back.hidden = showingBack;
    hint.textContent = showingBack ? "Click to reveal" : "Click to hide";
    element.setAttribute("aria-pressed", String(!showingBack));
    element.classList.toggle("is-flipped", !showingBack);
  });

  return element;
}

function renderFlashcards(container, cards) {
  container.replaceChildren();

  const grid = document.createElement("div");
  grid.className = "flashcard-grid";
  cards.forEach((card) => grid.append(buildCard(card)));

  container.append(grid);
}

export function initFlashcards(documentId, onAuthError) {
  const button = document.getElementById("flashcards-button");
  const countSelect = document.getElementById("flashcard-count");
  const output = document.getElementById("flashcards-output");

  button.addEventListener("click", async () => {
    setBusy(button, true, "Generating…");
    renderLoading(output, "Writing your flashcards…");

    try {
      const result = await generateFlashcards(
        documentId,
        Number(countSelect.value)
      );
      renderFlashcards(output, result.flashcards);
    } catch (error) {
      if (onAuthError(error)) return;
      renderError(
        output,
        error instanceof ApiError
          ? error.message
          : "Could not generate flashcards."
      );
    } finally {
      setBusy(button, false);
    }
  });
}
