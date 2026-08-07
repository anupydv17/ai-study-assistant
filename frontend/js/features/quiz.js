/**
 * The Quiz tab.
 *
 * Renders questions, lets the student answer, then marks them.
 * The correct answers arrive with the questions, so marking happens entirely
 * in the browser — no second request.
 */

import { ApiError, generateQuiz } from "../api.js";
import { setBusy } from "../ui.js";
import { renderError, renderLoading } from "./shared.js";

/** Build the radio buttons for one question. */
function buildQuestion(question, index) {
  const block = document.createElement("li");
  block.className = "quiz-question";

  const text = document.createElement("p");
  text.className = "quiz-question-text";
  text.textContent = question.question;
  block.append(text);

  const options = document.createElement("div");
  options.className = "quiz-options";

  question.options.forEach((optionText, optionIndex) => {
    const label = document.createElement("label");
    label.className = "quiz-option";

    const input = document.createElement("input");
    input.type = "radio";
    // Grouping by name is what makes only one option selectable per question.
    input.name = `question-${index}`;
    input.value = String(optionIndex);

    const span = document.createElement("span");
    span.textContent = optionText;

    label.append(input, span);
    options.append(label);
  });

  block.append(options);

  // Built now, revealed after marking.
  const feedback = document.createElement("p");
  feedback.className = "quiz-feedback";
  feedback.hidden = true;
  block.append(feedback);

  return block;
}

/** Mark every question and show the score. */
function markQuiz(questions, listElement, scoreElement) {
  let correctCount = 0;

  questions.forEach((question, index) => {
    const block = listElement.children[index];
    const chosen = block.querySelector(`input[name="question-${index}"]:checked`);
    const feedback = block.querySelector(".quiz-feedback");

    const chosenIndex = chosen ? Number(chosen.value) : null;
    const isCorrect = chosenIndex === question.correct_index;

    if (isCorrect) correctCount += 1;

    // Colour every option so the student sees the right answer either way.
    block.querySelectorAll(".quiz-option").forEach((label, optionIndex) => {
      label.classList.remove("is-correct", "is-wrong");
      if (optionIndex === question.correct_index) {
        label.classList.add("is-correct");
      } else if (optionIndex === chosenIndex) {
        label.classList.add("is-wrong");
      }
    });

    feedback.textContent =
      (chosenIndex === null
        ? "Not answered. "
        : isCorrect
          ? "Correct. "
          : "Incorrect. ") + question.explanation;
    feedback.className = `quiz-feedback ${isCorrect ? "is-correct" : "is-wrong"}`;
    feedback.hidden = false;
  });

  scoreElement.textContent = `You scored ${correctCount} out of ${questions.length}.`;
  scoreElement.hidden = false;
}

function renderQuiz(container, questions) {
  container.replaceChildren();

  const list = document.createElement("ol");
  list.className = "quiz-list";
  questions.forEach((question, index) => list.append(buildQuestion(question, index)));

  const score = document.createElement("p");
  score.className = "quiz-score";
  score.hidden = true;

  const checkButton = document.createElement("button");
  checkButton.className = "button-link";
  checkButton.type = "button";
  checkButton.textContent = "Check answers";
  checkButton.addEventListener("click", () => {
    markQuiz(questions, list, score);
    checkButton.disabled = true;
  });

  container.append(list, checkButton, score);
}

export function initQuiz(documentId, onAuthError) {
  const button = document.getElementById("quiz-button");
  const countSelect = document.getElementById("quiz-count");
  const output = document.getElementById("quiz-output");

  button.addEventListener("click", async () => {
    setBusy(button, true, "Generating…");
    renderLoading(output, "Writing your quiz…");

    try {
      const result = await generateQuiz(documentId, Number(countSelect.value));
      renderQuiz(output, result.questions);
    } catch (error) {
      if (onAuthError(error)) return;
      renderError(
        output,
        error instanceof ApiError ? error.message : "Could not generate a quiz."
      );
    } finally {
      setBusy(button, false);
    }
  });
}
