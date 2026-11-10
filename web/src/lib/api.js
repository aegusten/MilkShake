// Browser-side API client. Calls go to this same origin; the SvelteKit
// server forwards /api and /uploads to the backend (see hooks.server.js),
// so there is no CORS and no backend URL baked into the bundle.

const TOKEN_KEY = 'ms_admin_token';

const storage = {
  get(key) {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key, value) {
    try {
      if (value) localStorage.setItem(key, value);
      else localStorage.removeItem(key);
    } catch {
      // Private mode or blocked storage. The app still works for this visit.
    }
  },
};

export const getToken = () => storage.get(TOKEN_KEY);
export const setToken = (token) => storage.set(TOKEN_KEY, token);
export { storage };

async function request(path, { method = 'GET', body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
    });
  } catch {
    return { ok: false, status: 0, data: { detail: 'Network error. Check the connection.' } };
  }
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (response.status === 401) setToken(null);
  return { ok: response.ok, status: response.status, data };
}

export const api = {
  login: async (email, password) => {
    const res = await request('/api/admin/login', { method: 'POST', body: { email, password } });
    if (res.ok && res.data?.access_token) setToken(res.data.access_token);
    return res;
  },
  logout: () => setToken(null),
  isLoggedIn: () => Boolean(getToken()),

  drinks: () => request('/api/drinks'),
  itemMasters: () => request('/api/item-masters'),
  createItemMaster: (payload) => request('/api/admin/item-masters', { method: 'POST', body: payload }),
  updateItemMaster: (id, payload) =>
    request(`/api/admin/item-masters/${id}`, { method: 'PATCH', body: payload }),
  deleteItemMaster: (id) => request(`/api/admin/item-masters/${id}`, { method: 'DELETE' }),
  createDrink: (payload) => request('/api/admin/drinks', { method: 'POST', body: payload }),
  updateDrink: (id, payload) => request(`/api/admin/drinks/${id}`, { method: 'PATCH', body: payload }),
  deleteDrink: (id) => request(`/api/admin/drinks/${id}`, { method: 'DELETE' }),
  uploadImage: (file) => {
    const form = new FormData();
    form.append('file', file);
    return request('/api/admin/uploads', { method: 'POST', form });
  },

  placeOrder: (payload) => request('/api/orders', { method: 'POST', body: payload }),
  guestOrder: (id) => request(`/api/orders/${id}`),
  changeOrderStatus: (id, action) => request(`/api/admin/orders/${id}/${action}`, { method: 'POST' }),
};

// --- Live streams ------------------------------------------------------------

// The server pings every 15s. Silence well past that means the connection is
// dead even if the socket still looks open, which happens when a proxy
// outlives the backend, so we tear it down and reconnect.
const STALE_AFTER_MS = 40000;

/**
 * EventSource that survives anything. The browser's own retry gives up for
 * good on an HTTP error and never notices a silently dead proxy, so this
 * wraps it with a watchdog and its own backoff. ``handlers`` maps event name
 * to a function taking the parsed data. Returns a stop function.
 */
export function liveEvents(path, handlers, onStatus) {
  let source = null;
  let watchdog = null;
  let retry = null;
  let delay = 1000;
  let stopped = false;

  const reconnect = () => {
    source?.close();
    clearTimeout(watchdog);
    if (stopped) return;
    onStatus?.('reconnecting');
    retry = setTimeout(open, delay);
    delay = Math.min(delay * 2, 15000);
  };

  const alive = () => {
    clearTimeout(watchdog);
    watchdog = setTimeout(reconnect, STALE_AFTER_MS);
  };

  function open() {
    source = new EventSource(path);
    source.onopen = () => {
      delay = 1000;
      onStatus?.('live');
      alive();
    };
    source.addEventListener('ping', alive);
    for (const [name, fn] of Object.entries(handlers)) {
      source.addEventListener(name, (e) => {
        alive();
        fn(JSON.parse(e.data));
      });
    }
    source.onerror = reconnect;
  }

  open();
  return () => {
    stopped = true;
    clearTimeout(watchdog);
    clearTimeout(retry);
    source?.close();
  };
}

async function readEvents(body, onEvent) {
  const reader = body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer += value;
    let split;
    while ((split = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      let event = 'message';
      const data = [];
      for (const line of block.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7);
        else if (line.startsWith('data: ')) data.push(line.slice(6));
      }
      if (data.length) onEvent({ event, data: JSON.parse(data.join('\n')) });
    }
  }
}

/**
 * Live staff feed. EventSource cannot send an Authorization header, so this
 * reads the stream with fetch. Same watchdog and backoff as liveEvents.
 */
export function streamAdminOrders({ onEvent, onStatus, onUnauthorized }) {
  let stopped = false;
  let controller = null;
  let delay = 1000;

  (async () => {
    while (!stopped) {
      controller = new AbortController();
      try {
        const response = await fetch('/api/stream/admin', {
          headers: { Authorization: `Bearer ${getToken()}` },
          signal: controller.signal,
        });
        if (response.status === 401) {
          setToken(null);
          onUnauthorized?.();
          return;
        }
        if (!response.ok || !response.body) throw new Error(`stream ${response.status}`);
        onStatus?.('live');
        delay = 1000;
        let watchdog = setTimeout(() => controller.abort(), STALE_AFTER_MS);
        await readEvents(response.body, (message) => {
          clearTimeout(watchdog);
          watchdog = setTimeout(() => controller.abort(), STALE_AFTER_MS);
          if (message.event !== 'ping') onEvent(message);
        });
        clearTimeout(watchdog);
      } catch {
        if (stopped) return;
      }
      onStatus?.('reconnecting');
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, 15000);
    }
  })();

  return () => {
    stopped = true;
    controller?.abort();
  };
}
