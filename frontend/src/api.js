/* Frontend API client for the FastAPI backend. */

const DEFAULT_LOCAL_API = 'http://localhost:8000';

const apiBase = () => {
  const configured = window.MIAO_API_BASE_URL || import.meta.env.VITE_MIAO_API_BASE_URL;
  if (configured && configured.trim()) return configured.trim().replace(/\/$/, '');
  const host = window.location.hostname;
  if (window.location.protocol === 'file:' || host === 'localhost' || host === '127.0.0.1') {
    return DEFAULT_LOCAL_API;
  }
  return '';
};

export class ApiError extends Error {
  constructor(message, data, status) {
    super(message);
    this.name = 'ApiError';
    this.data = data || {};
    this.status = status;
    this.code = this.data.code || null;
  }
}

const request = async (path, options = {}) => {
  const res = await fetch(apiBase() + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_err) {
      data = { detail: text };
    }
  }
  if (!res.ok) {
    throw new ApiError(data?.detail || 'API request failed', data, res.status);
  }
  return data;
};

const stockText = {
  in: '現貨供應',
  low: '剩量不多',
  out: '已售完',
};

const normalizeProduct = (product) => ({
  id: product.id,
  slug: product.slug,
  name: product.name,
  sub: product.sub || 'Kanro · 蜜糖之味',
  desc: product.description,
  images: product.images || [],
  season: product.season,
  specs: (product.specs || []).map((spec) => ({
    id: spec.id,
    label: spec.label,
    qty: spec.qty_text,
    price: spec.price,
    stock: spec.stock_status,
    stockText: stockText[spec.stock_status] || '狀態確認中',
    note: spec.note,
    images: spec.images || [],
  })),
});

export const listProducts = async () => {
  const products = await request('/api/products');
  return products.map(normalizeProduct);
};

export const createOrder = (payload) => request('/api/orders', {
  method: 'POST',
  body: JSON.stringify(payload),
});

const authHeaders = (token) => ({
  Authorization: `Bearer ${token}`,
});

export const loginAdmin = async (username, password) => {
  const body = new URLSearchParams();
  body.set('username', username);
  body.set('password', password);
  const res = await fetch(apiBase() + '/api/admin/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(data?.detail || '登入失敗', data, res.status);
  return data;
};

export const getCurrentAdmin = (token) => request('/api/admin/auth/me', {
  headers: authHeaders(token),
});

const adminRequest = (token, path, options = {}) =>
  request(path, {
    ...options,
    headers: { ...authHeaders(token), ...(options.headers || {}) },
  });

// ── Admin products ──

export const listAdminProducts = (token) =>
  adminRequest(token, '/api/admin/products');

export const updateAdminProduct = (token, productId, data) =>
  adminRequest(token, `/api/admin/products/${productId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

// ── Admin image APIs ──

export const signUpload = (token, filename, contentType) =>
  adminRequest(token, '/api/admin/uploads/sign', {
    method: 'POST',
    body: JSON.stringify({ filename, content_type: contentType }),
  });

export const listProductImages = (token, productId) =>
  adminRequest(token, `/api/admin/products/${productId}/images`);

export const registerProductImage = (token, productId, url, sortOrder = 0) =>
  adminRequest(token, `/api/admin/products/${productId}/images`, {
    method: 'POST',
    body: JSON.stringify({ url, sort_order: sortOrder }),
  });

export const deleteProductImage = (token, imageId) =>
  adminRequest(token, `/api/admin/images/${imageId}`, { method: 'DELETE' });

export const reorderProductImages = (token, productId, items) =>
  adminRequest(token, `/api/admin/products/${productId}/images/reorder`, {
    method: 'PATCH',
    body: JSON.stringify({ items }),
  });

// ── Admin spec image APIs ──

export const listSpecImages = (token, specId) =>
  adminRequest(token, `/api/admin/specs/${specId}/images`);

export const registerSpecImage = (token, specId, url, sortOrder = 0) =>
  adminRequest(token, `/api/admin/specs/${specId}/images`, {
    method: 'POST',
    body: JSON.stringify({ url, sort_order: sortOrder }),
  });

export const reorderSpecImages = (token, specId, items) =>
  adminRequest(token, `/api/admin/specs/${specId}/images/reorder`, {
    method: 'PATCH',
    body: JSON.stringify({ items }),
  });

// ── Admin spec CRUD ──

export const createSpec = (token, productId, data) =>
  adminRequest(token, `/api/admin/products/${productId}/specs`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateSpec = (token, specId, data) =>
  adminRequest(token, `/api/admin/specs/${specId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const deleteSpec = (token, specId) =>
  adminRequest(token, `/api/admin/specs/${specId}`, { method: 'DELETE' });

export const listAdminOrders = (token, filters = {}) => {
  const qs = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      qs.set(key, value);
    }
  });
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return request(`/api/admin/orders${suffix}`, {
    headers: authHeaders(token),
  });
};

export const getAdminOrder = (token, orderNo) => request(
  `/api/admin/orders/${encodeURIComponent(orderNo)}`,
  {
    headers: authHeaders(token),
  }
);

export const updateAdminOrderStatus = (token, orderNo, status) => request(
  `/api/admin/orders/${encodeURIComponent(orderNo)}/status`,
  {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify({ status }),
  }
);

window.MiaoApi = {
  ApiError,
  createOrder,
  createSpec,
  deleteProductImage,
  deleteSpec,
  getAdminOrder,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listProductImages,
  listProducts,
  listSpecImages,
  loginAdmin,
  registerProductImage,
  registerSpecImage,
  reorderProductImages,
  reorderSpecImages,
  signUpload,
  updateAdminOrderStatus,
  updateAdminProduct,
  updateSpec,
};
