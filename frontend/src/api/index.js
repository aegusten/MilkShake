const API_BASE = import.meta.env.VITE_API_BASE || "";
const TOKEN_KEY = "ms_admin_token";

const getToken = () => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
};

const setToken = (token) => {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
};

const apiFetch = async (path, { method = "GET", body } = {}) => {
  const headers = {};
  if (body) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }
  if (response.status === 401) {
    setToken(null);
  }
  return { ok: response.ok, status: response.status, data };
};

export const loginAdmin = async (email, password) => {
  const response = await apiFetch("/api/admin/login", {
    method: "POST",
    body: { email, password },
  });
  if (response.ok && response.data?.access_token) {
    setToken(response.data.access_token);
  }
  return response;
};

export const logoutAdmin = () => {
  setToken(null);
};

export const isAdminLoggedIn = () => Boolean(getToken());

export const fetchItemMasters = () => apiFetch("/api/item-masters");

export const fetchDrinks = () => apiFetch("/api/drinks");

export const createOrder = (payload) =>
  apiFetch("/api/orders", {
    method: "POST",
    body: payload,
  });

export const createItemMaster = (payload) =>
  apiFetch("/api/admin/item-masters", {
    method: "POST",
    body: payload,
  });

export const updateItemMaster = (id, payload) =>
  apiFetch(`/api/admin/item-masters/${id}`, {
    method: "PATCH",
    body: payload,
  });

export const deleteItemMaster = (id) =>
  apiFetch(`/api/admin/item-masters/${id}`, {
    method: "DELETE",
  });

export const createDrink = (payload) =>
  apiFetch("/api/admin/drinks", {
    method: "POST",
    body: payload,
  });

export const updateDrink = (id, payload) =>
  apiFetch(`/api/admin/drinks/${id}`, {
    method: "PATCH",
    body: payload,
  });

export const deleteDrink = (id) =>
  apiFetch(`/api/admin/drinks/${id}`, {
    method: "DELETE",
  });

export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const headers = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE}/api/admin/uploads`, {
    method: "POST",
    headers,
    body: formData,
  });
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }
  if (response.status === 401) {
    setToken(null);
  }
  return { ok: response.ok, status: response.status, data };
};

export const fetchAdminOrders = (statuses = []) => {
  const query = statuses.map((s) => `status=${encodeURIComponent(s)}`).join("&");
  return apiFetch(`/api/admin/orders${query ? `?${query}` : ""}`);
};

// action is one of accept, ready, complete, cancel.
export const changeOrderStatus = (orderId, action) =>
  apiFetch(`/api/admin/orders/${orderId}/${action}`, { method: "POST" });

export const fetchGuestOrder = (orderId) => apiFetch(`/api/orders/${orderId}`);

// Splits a text/event-stream body into { event, data } objects.
const readEvents = async (body, onEvent) => {
  const reader = body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) {
      return;
    }
    buffer += value;
    let split;
    while ((split = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      let event = "message";
      const data = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data.push(line.slice(6));
      }
      if (data.length) {
        onEvent({ event, data: JSON.parse(data.join("\n")) });
      }
    }
  }
};

// The server sends a ping every 15s. Silence well past that means the
// connection is dead even if the socket still looks open, which happens when
// a proxy outlives the backend, so callers tear it down and reconnect.
const STALE_AFTER_MS = 40000;

/**
 * EventSource that survives anything. The browser's own retry gives up for
 * good on an HTTP error, and never notices a silently dead proxy, so this
 * wraps it with a watchdog and its own backoff. handlers maps event name to
 * a function taking the parsed data.
 */
export const liveEvents = (path, handlers, onStatus) => {
  let source = null;
  let watchdog = null;
  let retry = null;
  let delay = 1000;
  let stopped = false;

  const reconnect = () => {
    source?.close();
    clearTimeout(watchdog);
    if (stopped) return;
    onStatus?.("reconnecting");
    retry = setTimeout(open, delay);
    delay = Math.min(delay * 2, 15000);
  };

  const alive = () => {
    clearTimeout(watchdog);
    watchdog = setTimeout(reconnect, STALE_AFTER_MS);
  };

  const open = () => {
    source = new EventSource(`${API_BASE}${path}`);
    source.onopen = () => {
      delay = 1000;
      onStatus?.("live");
      alive();
    };
    source.addEventListener("ping", alive);
    for (const [name, fn] of Object.entries(handlers)) {
      source.addEventListener(name, (e) => {
        alive();
        fn(JSON.parse(e.data));
      });
    }
    source.onerror = reconnect;
  };

  open();
  return () => {
    stopped = true;
    clearTimeout(watchdog);
    clearTimeout(retry);
    source?.close();
  };
};

/**
 * Live staff feed. EventSource cannot send an Authorization header, so this
 * reads the stream with fetch instead. Reconnects with backoff until stop()
 * is called; every reconnect starts with a fresh snapshot event.
 */
export const streamAdminOrders = ({ onEvent, onStatus, onUnauthorized }) => {
  let stopped = false;
  let controller = null;
  let delay = 1000;

  const run = async () => {
    while (!stopped) {
      controller = new AbortController();
      try {
        const response = await fetch(`${API_BASE}/api/stream/admin`, {
          headers: { Authorization: `Bearer ${getToken()}` },
          signal: controller.signal,
        });
        if (response.status === 401) {
          setToken(null);
          onUnauthorized?.();
          return;
        }
        if (!response.ok || !response.body) {
          throw new Error(`stream ${response.status}`);
        }
        onStatus?.("live");
        delay = 1000;
        let watchdog = setTimeout(() => controller.abort(), STALE_AFTER_MS);
        await readEvents(response.body, (message) => {
          clearTimeout(watchdog);
          watchdog = setTimeout(() => controller.abort(), STALE_AFTER_MS);
          if (message.event !== "ping") onEvent(message);
        });
        clearTimeout(watchdog);
      } catch (error) {
        if (stopped) return;
      }
      onStatus?.("reconnecting");
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, 15000);
    }
  };

  run();
  return () => {
    stopped = true;
    controller?.abort();
  };
};

export { API_BASE };
