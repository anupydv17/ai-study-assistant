/**
 * Formatting helpers.
 *
 * The API sends raw numbers and ISO timestamps. Turning those into something
 * a human wants to read is presentation work, so it belongs on the frontend.
 */

/** 2003 -> "2.0 KB" */
export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** "2026-08-06T16:09:07" -> "6 Aug 2026" */
export function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** 1 -> "1 page", 3 -> "3 pages" */
export function formatPages(count) {
  if (count === null || count === undefined) return "unknown length";
  return count === 1 ? "1 page" : `${count} pages`;
}
