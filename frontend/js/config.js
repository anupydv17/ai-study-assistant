/**
 * Frontend configuration.
 *
 * This is a static site with no build step, so there is no way to inject an
 * environment variable at build time. Instead we pick the API URL from the
 * hostname the page is being served from.
 *
 * After deploying the backend, replace PRODUCTION_API_URL with your Render
 * URL. That is the only line you need to change.
 */

const LOCAL_API_URL = "http://127.0.0.1:8000/api/v1";
const PRODUCTION_API_URL = "https://study-assistant-api.onrender.com/api/v1";

/** True when the page is being served from your own machine. */
function isLocal() {
  const { hostname } = window.location;
  return hostname === "localhost" || hostname === "127.0.0.1";
}

export const API_BASE_URL = isLocal() ? LOCAL_API_URL : PRODUCTION_API_URL;

/** Key used to store the access token in localStorage. */
export const TOKEN_KEY = "study_assistant_token";
