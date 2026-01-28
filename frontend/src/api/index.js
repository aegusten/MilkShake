const API_BASE = import.meta.env.VITE_API_BASE || "";

const apiFetch = async (path, { method = "GET", body, adminId } = {}) => {
  const headers = {};
  if (body) {
    headers["Content-Type"] = "application/json";
  }
  if (adminId) {
    headers["X-Admin-Id"] = adminId;
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
  return { ok: response.ok, status: response.status, data };
};

export const loginAdmin = (email, password) =>
  apiFetch("/api/admin/login", {
    method: "POST",
    body: { email, password },
  });

export const fetchItemMasters = () => apiFetch("/api/item-masters");

export const fetchDrinks = () => apiFetch("/api/drinks");

export const createOrder = (payload) =>
  apiFetch("/api/orders", {
    method: "POST",
    body: payload,
  });

export const createItemMaster = (adminId, payload) =>
  apiFetch("/api/admin/item-masters", {
    method: "POST",
    adminId,
    body: payload,
  });

export const updateItemMaster = (adminId, id, payload) =>
  apiFetch(`/api/admin/item-masters/${id}`, {
    method: "PATCH",
    adminId,
    body: payload,
  });

export const deleteItemMaster = (adminId, id) =>
  apiFetch(`/api/admin/item-masters/${id}`, {
    method: "DELETE",
    adminId,
  });

export const createDrink = (adminId, payload) =>
  apiFetch("/api/admin/drinks", {
    method: "POST",
    adminId,
    body: payload,
  });

export const updateDrink = (adminId, id, payload) =>
  apiFetch(`/api/admin/drinks/${id}`, {
    method: "PATCH",
    adminId,
    body: payload,
  });

export const deleteDrink = (adminId, id) =>
  apiFetch(`/api/admin/drinks/${id}`, {
    method: "DELETE",
    adminId,
  });

export const uploadImage = async (adminId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/admin/uploads`, {
    method: "POST",
    headers: adminId ? { "X-Admin-Id": adminId } : {},
    body: formData,
  });
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }
  return { ok: response.ok, status: response.status, data };
};

export { API_BASE };

export const fetchAdminOrders = (adminId) =>
  apiFetch("/api/admin/orders", { adminId });
