import { backendJson } from '$lib/server/backend.js';

/** The menu renders on the server, so a guest on a slow connection sees
 *  drinks and prices in the first response instead of a blank page. */
export async function load({ fetch, setHeaders }) {
  try {
    const [drinks, itemMasters] = await Promise.all([
      backendJson(fetch, '/api/drinks'),
      backendJson(fetch, '/api/item-masters'),
    ]);
    // Short shared cache: the menu changes rarely, orders never touch it.
    setHeaders({ 'cache-control': 'public, max-age=30' });
    return { drinks, itemMasters, loadFailed: false };
  } catch {
    return { drinks: [], itemMasters: [], loadFailed: true };
  }
}
