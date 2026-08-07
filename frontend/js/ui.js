/**
 * Small helpers shared by every page.
 */

/** Show a message in the page's message element. */
export function showMessage(text, type = "error") {
  const element = document.getElementById("message");
  element.textContent = text;
  element.className = `message ${type}`;
  element.hidden = false;
}

/** Hide the message element. */
export function hideMessage() {
  document.getElementById("message").hidden = true;
}

/**
 * Disable a button while work is happening and restore it afterwards.
 *
 * Without this, a user can click "Log in" five times and send five requests.
 */
export function setBusy(button, isBusy, busyLabel = "Please wait…") {
  if (isBusy) {
    button.dataset.idleLabel = button.textContent;
    button.textContent = busyLabel;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.idleLabel ?? button.textContent;
    button.disabled = false;
  }
}
