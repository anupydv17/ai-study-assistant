/**
 * The Summary tab.
 */

import { ApiError, generateSummary } from "../api.js";
import { setBusy } from "../ui.js";
import { renderError, renderLoading, renderRichText } from "./shared.js";

export function initSummary(documentId, onAuthError) {
  const button = document.getElementById("summary-button");
  const output = document.getElementById("summary-output");

  button.addEventListener("click", async () => {
    setBusy(button, true, "Generating…");
    renderLoading(output, "Writing your summary…");

    try {
      const result = await generateSummary(documentId);
      renderRichText(output, result.summary);
    } catch (error) {
      if (onAuthError(error)) return;
      renderError(
        output,
        error instanceof ApiError ? error.message : "Could not generate a summary."
      );
    } finally {
      setBusy(button, false);
    }
  });
}
