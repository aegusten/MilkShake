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

export const fetchAdminOrders = () => apiFetch("/api/admin/orders");

export { API_BASE };
