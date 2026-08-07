/**
 * A thin wrapper around fetch() for talking to the backend.
 *
 * Every network call in the app goes through this file, so the token,
 * the base URL and error handling exist in exactly one place. Page scripts
 * never call fetch() directly.
 */

import { API_BASE_URL, TOKEN_KEY } from "./config.js";

/* ------------------------------------------------------------------ */
/* Token storage                                                       */
/* ------------------------------------------------------------------ */

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn() {
  return Boolean(getToken());
}

/* ------------------------------------------------------------------ */
/* Errors                                                              */
/* ------------------------------------------------------------------ */

/**
 * An error carrying the HTTP status, so callers can react to *why* a
 * request failed rather than just that it did.
 */
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Turn FastAPI's error body into one readable sentence.
 *
 * FastAPI returns `detail` as a string for errors we raise ourselves, but as
 * an array of objects for validation failures (422). Both are handled here so
 * no page has to know the difference.
 */
function readErrorMessage(body, status) {
  const detail = body?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    // loc looks like ["body", "email"] — the last entry is the field name.
    return detail
      .map((item) => {
        const field = item.loc?.[item.loc.length - 1] ?? "field";
        return `${field}: ${item.msg}`;
      })
      .join("\n");
  }

  return `Request failed (HTTP ${status}).`;
}

/* ------------------------------------------------------------------ */
/* The request function                                                */
/* ------------------------------------------------------------------ */

/**
 * Make a request to the API.
 *
 * @param {string} path      Path after /api/v1, e.g. "/auth/login"
 * @param {object} options
 * @param {string} [options.method]  HTTP method, defaults to GET
 * @param {object} [options.json]    Body to send as JSON
 * @param {object} [options.form]    Body to send as form-encoded data
 * @param {boolean} [options.auth]   Attach the token, defaults to true
 * @returns {Promise<any>} Parsed JSON, or null for 204 responses
 */
export async function apiRequest(path, options = {}) {
  const { method = "GET", json, form, formData, auth = true } = options;

  const headers = {};
  let body;

  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form !== undefined) {
    // The login endpoint follows the OAuth2 standard, which requires
    // form-encoded data rather than JSON.
    body = new URLSearchParams(form);
  } else if (formData !== undefined) {
    // File uploads. We deliberately do NOT set Content-Type here: the browser
    // must generate it itself, because multipart requires a random boundary
    // string that only the browser knows.
    body = formData;
  }

  if (auth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { method, headers, body });
  } catch {
    // fetch() only rejects when the request never completed: the server is
    // down, the network is off, or CORS blocked it.
    throw new ApiError(
      0,
      "Cannot reach the server. Check that the backend is running."
    );
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, readErrorMessage(data, response.status));
  }

  return data;
}

/* ------------------------------------------------------------------ */
/* Endpoint helpers                                                    */
/* ------------------------------------------------------------------ */

export function register({ email, fullName, password }) {
  return apiRequest("/auth/register", {
    method: "POST",
    auth: false,
    json: { email, full_name: fullName, password },
  });
}

export async function login({ email, password }) {
  // OAuth2 names the field "username"; we put the email in it.
  const data = await apiRequest("/auth/login", {
    method: "POST",
    auth: false,
    form: { username: email, password },
  });

  saveToken(data.access_token);
  return data;
}

export function getCurrentUser() {
  return apiRequest("/users/me");
}

export function updateProfile(fullName) {
  return apiRequest("/users/me", {
    method: "PATCH",
    json: { full_name: fullName },
  });
}

export function changePassword(currentPassword, newPassword) {
  return apiRequest("/users/me/password", {
    method: "POST",
    json: { current_password: currentPassword, new_password: newPassword },
  });
}

export function deleteAccount() {
  return apiRequest("/users/me", { method: "DELETE" });
}

export function logout() {
  clearToken();
}

/* ---------- Documents ---------- */

export function listDocuments() {
  return apiRequest("/documents");
}

export function getDocument(documentId) {
  return apiRequest(`/documents/${documentId}`);
}

export function uploadDocument(file) {
  // FormData builds the multipart body. The field name "file" must match the
  // parameter name in the FastAPI endpoint.
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest("/documents/upload", { method: "POST", formData });
}

export function deleteDocument(documentId) {
  return apiRequest(`/documents/${documentId}`, { method: "DELETE" });
}

/* ---------- AI study tools ---------- */

export function generateSummary(documentId) {
  return apiRequest(`/documents/${documentId}/summary`, { method: "POST" });
}

export function generateQuiz(documentId, count = 5) {
  return apiRequest(`/documents/${documentId}/quiz?count=${count}`, {
    method: "POST",
  });
}

export function generateFlashcards(documentId, count = 10) {
  return apiRequest(`/documents/${documentId}/flashcards?count=${count}`, {
    method: "POST",
  });
}

/* ---------- Chat ---------- */

export function getChatHistory(documentId) {
  return apiRequest(`/documents/${documentId}/chat`);
}

export function askQuestion(documentId, question) {
  return apiRequest(`/documents/${documentId}/chat`, {
    method: "POST",
    json: { question },
  });
}

export function clearChat(documentId) {
  return apiRequest(`/documents/${documentId}/chat`, { method: "DELETE" });
}
