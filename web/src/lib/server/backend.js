import { env } from '$env/dynamic/private';

// Where the FastAPI backend is reachable from this server. Inside compose
// that is the service name; never exposed to the browser.
export const BACKEND_URL = (env.BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');

/** GET a backend JSON endpoint from server code (SSR loads). */
export async function backendJson(fetchFn, path) {
  const response = await fetchFn(`${BACKEND_URL}${path}`);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}
