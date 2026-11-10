import { backendJson } from '$lib/server/backend.js';

/** The menu renders on the server, so a guest on a slow connection sees
 *  drinks and prices in the first response instead of a blank page.
 *
 *  No cache-control here on purpose: the HTML is rendered in the language
 *  from the guest's cookie, and a cached copy served the previous language
 *  after a switch. */
export async function load({ fetch }) {
  try {
    const [drinks, itemMasters] = await Promise.all([
      backendJson(fetch, '/api/drinks'),
      backendJson(fetch, '/api/item-masters'),
    ]);
    return { drinks, itemMasters, loadFailed: false };
  } catch {
    return { drinks: [], itemMasters: [], loadFailed: true };
  }
}
