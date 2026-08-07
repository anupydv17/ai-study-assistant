/**
 * Helpers shared by the study-tool features.
 */

/**
 * Replace a container's contents with a loading state.
 *
 * AI calls take 8-15 seconds. Showing a spinner AND telling the user roughly
 * how long to expect is what stops the page reading as broken.
 */
export function renderLoading(container, label) {
  container.replaceChildren();

  const wrapper = document.createElement("div");
  wrapper.className = "loading";

  const spinner = document.createElement("div");
  spinner.className = "spinner";

  const text = document.createElement("p");
  text.className = "loading-text";
  text.textContent = label;

  const hint = document.createElement("p");
  hint.className = "panel-hint";
  hint.textContent = "This usually takes 10–15 seconds.";

  wrapper.append(spinner, text, hint);
  container.append(wrapper);
}

/** Replace a container's contents with an error message. */
export function renderError(container, text) {
  container.replaceChildren();

  const paragraph = document.createElement("p");
  paragraph.className = "message error";
  paragraph.textContent = text;

  container.append(paragraph);
}

/**
 * Render text that may contain simple markdown-style bullets and bold.
 *
 * Deliberately minimal and built with createElement rather than innerHTML:
 * this text comes from an AI reading a user-supplied PDF, so it is untrusted.
 */
export function renderRichText(container, text) {
  container.replaceChildren();

  for (const block of text.split("\n\n")) {
    const lines = block.split("\n").filter((line) => line.trim());
    if (lines.length === 0) continue;

    const isBulletList = lines.every((line) => /^\s*[-*•]\s+/.test(line));

    if (isBulletList) {
      const list = document.createElement("ul");
      for (const line of lines) {
        const item = document.createElement("li");
        item.textContent = stripFormatting(line.replace(/^\s*[-*•]\s+/, ""));
        list.append(item);
      }
      container.append(list);
    } else {
      const paragraph = document.createElement("p");
      paragraph.textContent = stripFormatting(lines.join(" "));
      container.append(paragraph);
    }
  }
}

/** Remove markdown ** and * markers, since we render as plain text. */
function stripFormatting(text) {
  return text.replace(/\*\*(.+?)\*\*/g, "$1").replace(/\*(.+?)\*/g, "$1");
}
