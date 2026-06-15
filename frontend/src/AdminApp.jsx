/* Admin order management — redesigned 2026-06-14 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  deleteProductImage,
  getAdminOrder,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listSpecImages,
  loginAdmin,
  registerSpecImage,
  signUpload,
  updateAdminOrderStatus,
  updateSpec,
} from './api.js';

const TOKEN_KEY = 'miao.admin.token';

const STATUS_LABELS = {
  pending_payment: '待付款',
  pending: '待確認',
  confirmed: '已確認',
  shipping: '出貨中',
  delivered: '已送達',
  cancelled: '已取消',
};

const NEXT_STATUS = {
  pending_payment: ['confirmed', 'cancelled'],
  pending: ['confirmed', 'cancelled'],
  confirmed: ['shipping', 'cancelled'],
  shipping: ['delivered'],
  delivered: [],
  cancelled: [],
};

const CHIP_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'pending_payment', label: '待付款' },
  { value: 'pending', label: '待確認' },
  { value: 'confirmed', label: '已確認' },
  { value: 'shipping', label: '出貨中' },
  { value: 'delivered', label: '已送達' },
  { value: 'cancelled', label: '已取消' },
];

const money = (n) => `NT$ ${Number(n || 0).toLocaleString()}`;
const dateText = (s) =>
  s ? new Date(s).toLocaleString('zh-TW', { hour12: false }) : '—';
const statusLabel = (s) => STATUS_LABELS[s] || s || '—';

/* ── Resolve search text → API params ──
   If the input looks like an order number (starts with MM-), send as order_no
   (exact match). Otherwise send as q (name + phone ilike). */
function resolveSearchParams(filters) {
  const params = {};
  if (filters.status) params.status = filters.status;
  if (filters.date_from) params.date_from = filters.date_from;
  if (filters.date_to) params.date_to = filters.date_to;
  const text = (filters.searchText ?? '').trim();
  if (text) {
    if (/^MM-/i.test(text)) {
      params.order_no = text;
    } else {
      params.q = text;
    }
  }
  return params;
}

/* ── Alert ── */
function Alert({ message }) {
  if (!message) return null;
  return <div className="adm-alert">{message}</div>;
}

/* ── Status badge ── */
function StatusBadge({ status, large }) {
  const base = large ? 'adm-badge-lg' : 'adm-badge';
  return (
    <span className={`${base} adm-badge--${status}`}>
      {statusLabel(status)}
    </span>
  );
}

/* ── Login view ── */
function LoginView({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const token = await loginAdmin(username, password);
      onLogin(token.access_token);
    } catch (err) {
      setError(err?.data?.detail || '登入失敗，請確認帳號密碼。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="adm-login">
      <div className="adm-login__box">
        <div className="adm-login__header">
          <p className="adm-login__eyebrow">Miao Fruit Shop</p>
          <h1 className="adm-login__title">後台管理</h1>
        </div>
        <form className="adm-login__form" onSubmit={submit}>
          <label className="adm-login__label">
            帳號
            <input
              className="adm-login__input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="adm-login__label">
            密碼
            <input
              className="adm-login__input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          <Alert message={error} />
          <button
            className="adm-login__submit"
            disabled={loading || !username || !password}
          >
            {loading ? '登入中…' : '登入'}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ── Filter strip ── */
function FilterStrip({ totalAll, filters, setFilters, onSearch }) {
  const debounceRef = useRef(null);
  useEffect(() => () => clearTimeout(debounceRef.current), []);

  const setChipStatus = (value) => {
    const next = { ...filters, status: value };
    setFilters(next);
    onSearch(next);
  };

  const setSearchText = (value) => {
    const next = { ...filters, searchText: value };
    setFilters(next);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => onSearch(next), 300);
  };

  const setDate = (key, value) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    onSearch(next);
  };

  return (
    <div className="adm-filters">
      <div className="adm-chips">
        {CHIP_OPTIONS.map(({ value, label }) => (
          <button
            key={value}
            className={`adm-chip${filters.status === value ? ' adm-chip--active' : ''}`}
            onClick={() => setChipStatus(value)}
          >
            {label}
            {value === '' && (
              <span className="adm-chip__count">{totalAll}</span>
            )}
          </button>
        ))}
      </div>
      <div className="adm-search-row">
        <div className="adm-search">
          <svg
            className="adm-search__icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            className="adm-search__input"
            placeholder="搜尋姓名、電話、訂單編號…"
            value={filters.searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
        <div className="adm-date-range">
          <input
            className="adm-date-input"
            type="date"
            value={filters.date_from}
            onChange={(e) => setDate('date_from', e.target.value)}
          />
          <span className="adm-date-sep">—</span>
          <input
            className="adm-date-input"
            type="date"
            value={filters.date_to}
            onChange={(e) => setDate('date_to', e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

/* ── Orders table ── */
function OrdersTable({ orders, selectedOrderNo, onSelect }) {
  if (orders.length === 0) {
    return (
      <div className="adm-table-card">
        <div className="adm-empty">沒有符合條件的訂單</div>
      </div>
    );
  }
  return (
    <div className="adm-table-card">
      <table className="adm-table">
        <thead>
          <tr>
            <th>訂單編號</th>
            <th>狀態</th>
            <th>收件人</th>
            <th>電話</th>
            <th className="adm-num">金額</th>
            <th>建立時間</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr
              key={order.order_no}
              className={selectedOrderNo === order.order_no ? 'is-selected' : ''}
              onClick={() => onSelect(order.order_no)}
            >
              <td><span className="adm-mono">{order.order_no}</span></td>
              <td><StatusBadge status={order.status} /></td>
              <td>{order.customer_name}</td>
              <td className="adm-muted">{order.customer_phone}</td>
              <td className="adm-num">{money(order.total)}</td>
              <td className="adm-muted">{dateText(order.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Order detail modal ── */
function OrderModal({ orderNo, token, onClose, onStatusChange }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusTarget, setStatusTarget] = useState('');
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    setDetail(null);
    setStatusTarget('');
    setUpdateError('');
    getAdminOrder(token, orderNo)
      .then((data) => { if (!cancelled) { setDetail(data); setLoading(false); } })
      .catch(() => { if (!cancelled) { setError('無法載入訂單明細。'); setLoading(false); } });
    return () => { cancelled = true; };
  }, [orderNo, token]);

  useEffect(() => { setStatusTarget(''); }, [detail?.status]);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  const nextStatuses = useMemo(
    () => (detail ? (NEXT_STATUS[detail.status] ?? []) : []),
    [detail?.status],
  );

  const handleUpdate = async () => {
    if (!statusTarget) return;
    setUpdating(true);
    setUpdateError('');
    try {
      const updated = await updateAdminOrderStatus(token, orderNo, statusTarget);
      setDetail(updated);
      onStatusChange();
    } catch (err) {
      setUpdateError(err?.data?.detail || '狀態更新失敗。');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="adm-modal-overlay" onClick={onClose}>
      <div className="adm-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="adm-modal__head">
          <div>
            <div className="adm-modal__order-no">{orderNo}</div>
            <div className="adm-modal__customer">
              {loading ? '載入中…' : (detail?.customer_name ?? '—')}
            </div>
          </div>
          <div className="adm-modal__head-right">
            {detail && <StatusBadge status={detail.status} large />}
            <button className="adm-modal__close" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Body */}
        {loading && (
          <div className="adm-modal__body" style={{ display: 'block' }}>
            <div className="adm-empty">載入明細中…</div>
          </div>
        )}
        {error && <p className="adm-modal__error">{error}</p>}
        {!loading && !error && detail && (
          <div className="adm-modal__body">
            {/* Left — 收件資訊 */}
            <div>
              <div className="adm-modal__section">
                <div className="adm-modal__section-title">收件資訊</div>
                <dl className="adm-modal__dl">
                  <dt>電話</dt><dd>{detail.customer_phone}</dd>
                  <dt>Email</dt><dd>{detail.customer_email || '—'}</dd>
                  <dt>地址</dt>
                  <dd>
                    {detail.ship_zipcode}&nbsp;
                    {detail.ship_city}{detail.ship_district}{detail.ship_street}
                  </dd>
                  <dt>希望送達</dt><dd>{detail.preferred_date}</dd>
                  <dt>配送時段</dt><dd>{detail.delivery_window}</dd>
                  <dt>付款方式</dt><dd>{detail.payment_method}</dd>
                  <dt>備註</dt><dd>{detail.note || '—'}</dd>
                </dl>
              </div>
            </div>
            {/* Right — 商品明細 */}
            <div>
              <div className="adm-modal__section">
                <div className="adm-modal__section-title">商品明細</div>
                <div className="adm-modal__items">
                  {detail.items.map((item, idx) => (
                    <div className="adm-modal__item" key={idx}>
                      <div>
                        <div className="adm-modal__item-name">{item.product_name}</div>
                        <div className="adm-modal__item-spec">
                          {item.spec_label} × {item.qty}
                        </div>
                      </div>
                      <div className="adm-modal__item-price">{money(item.line_total)}</div>
                    </div>
                  ))}
                </div>
                <div className="adm-modal__totals">
                  <span>小計</span><span>{money(detail.subtotal)}</span>
                  <span>運費</span><span>{money(detail.shipping_fee)}</span>
                  <span>貨到付款手續費</span><span>{money(detail.cod_fee)}</span>
                  <span className="grand">總計</span>
                  <span className="grand-val">{money(detail.total)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        {!loading && !error && detail && (
          <div className="adm-modal__foot">
            {updateError
              ? <span style={{ fontSize: 12, color: 'var(--packaging-red)', flex: 1 }}>{updateError}</span>
              : <span className="adm-modal__foot-label">變更狀態</span>
            }
            <select
              className="adm-modal__status-select"
              value={statusTarget}
              onChange={(e) => setStatusTarget(e.target.value)}
              disabled={nextStatuses.length === 0 || updating}
            >
              <option value="">
                {nextStatuses.length ? '選擇下一個狀態…' : '此訂單已不可變更'}
              </option>
              {nextStatuses.map((s) => (
                <option key={s} value={s}>{statusLabel(s)}</option>
              ))}
            </select>
            <button
              className="adm-modal__update-btn"
              disabled={!statusTarget || updating}
              onClick={handleUpdate}
            >
              {updating ? '更新中…' : '確認更新'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const STOCK_STATUS_LABELS = { in: '現貨供應', low: '剩量不多', out: '預購中' };
const STOCK_STATUS_OPTIONS = [
  { value: 'in', label: '現貨供應' },
  { value: 'low', label: '剩量不多' },
  { value: 'out', label: '預購中' },
];

/* ── Spec image gallery (規格層級) ── */
function SpecImageGallery({ specId, token }) {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listSpecImages(token, specId).then(setImages).catch(() => {});
  }, [specId, token]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const { signed_url, public_url } = await signUpload(token, file.name, file.type);
      await fetch(signed_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });
      const img = await registerSpecImage(token, specId, public_url, images.length);
      setImages((prev) => [...prev, img]);
    } catch (err) {
      setError('上傳失敗：' + (err?.message || '請稍後再試'));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (imageId) => {
    try {
      await deleteProductImage(token, imageId);
      setImages((prev) => prev.filter((i) => i.id !== imageId));
    } catch {
      setError('刪除失敗，請稍後再試');
    }
  };

  return (
    <div className="img-gallery">
      <div className="img-gallery__grid">
        {images.map((img) => (
          <div key={img.id} className="img-gallery__item">
            <img src={img.url} alt="" className="img-gallery__thumb" />
            <button
              className="img-gallery__delete"
              onClick={() => handleDelete(img.id)}
              title="移除"
            >✕</button>
          </div>
        ))}
        <label className={`img-gallery__upload-btn${uploading ? ' is-uploading' : ''}`}>
          {uploading ? '上傳中…' : '＋'}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            disabled={uploading}
          />
        </label>
      </div>
      {error && <div className="adm-alert" style={{ marginTop: 8 }}>{error}</div>}
    </div>
  );
}

/* ── Spec edit modal ── */
function SpecEditModal({ spec, token, onClose, onSaved }) {
  const [form, setForm] = useState({
    label: spec.label,
    qty_text: spec.qty_text,
    price: spec.price,
    stock_qty: spec.stock_qty,
    note: spec.note || '',
    is_active: spec.is_active,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  const setField = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await updateSpec(token, spec.id, {
        label: form.label,
        qty_text: form.qty_text,
        price: Number(form.price),
        stock_qty: Number(form.stock_qty),
        note: form.note || null,
        is_active: form.is_active,
      });
      onSaved();
    } catch (err) {
      setError(err?.data?.detail || '儲存失敗');
      setSaving(false);
    }
  };

  return (
    <div className="adm-modal-overlay" onClick={onClose}>
      <div className="adm-modal adm-modal--product" onClick={(e) => e.stopPropagation()}>
        <div className="adm-modal__head">
          <div>
            <div className="adm-modal__order-no">{spec.label}</div>
            <div className="adm-modal__customer">規格 ID: {spec.id}</div>
          </div>
          <button className="adm-modal__close" onClick={onClose}>✕</button>
        </div>
        <div className="adm-modal__product-body">
          {/* 圖片 */}
          <div className="adm-modal__section">
            <div className="adm-modal__section-title">規格圖片</div>
            <SpecImageGallery specId={spec.id} token={token} />
          </div>
          {/* 規格資訊 */}
          <div className="adm-modal__section">
            <div className="adm-modal__section-title">規格資訊</div>
            <div className="adm-spec-form">
              <label className="adm-field">
                <span className="adm-field__label">規格名稱</span>
                <input
                  className="adm-field__input"
                  value={form.label}
                  onChange={(e) => setField('label', e.target.value)}
                />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">容量說明</span>
                <input
                  className="adm-field__input"
                  value={form.qty_text}
                  onChange={(e) => setField('qty_text', e.target.value)}
                />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">售價（NT$）</span>
                <input
                  className="adm-field__input"
                  type="number"
                  min="0"
                  value={form.price}
                  onChange={(e) => setField('price', e.target.value)}
                />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">庫存數量</span>
                <input
                  className="adm-field__input"
                  type="number"
                  min="0"
                  value={form.stock_qty}
                  onChange={(e) => setField('stock_qty', e.target.value)}
                />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">備註</span>
                <input
                  className="adm-field__input"
                  value={form.note}
                  onChange={(e) => setField('note', e.target.value)}
                  placeholder="如：剩 3 箱"
                />
              </label>
              <label className="adm-field adm-field--row">
                <span className="adm-field__label">上架</span>
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setField('is_active', e.target.checked)}
                />
              </label>
            </div>
          </div>
          {error && <div className="adm-alert">{error}</div>}
        </div>
        <div className="adm-modal__foot">
          <span />
          <button className="adm-btn adm-btn--ghost" onClick={onClose}>取消</button>
          <button
            className="adm-modal__update-btn"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? '儲存中…' : '儲存'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Products tab — specs expanded under each product ── */
function ProductsTab({ token }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editSpec, setEditSpec] = useState(null);
  const [expanded, setExpanded] = useState({});

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listAdminProducts(token);
      setProducts(data);
      // auto-expand all products
      const exp = {};
      data.forEach((p) => { exp[p.id] = true; });
      setExpanded(exp);
    } catch {
      setError('無法載入商品資料');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [token]);

  if (loading) return <div className="adm-table-wrap"><div className="adm-empty">載入商品中…</div></div>;
  if (error) return <div className="adm-table-wrap"><div className="adm-alert">{error}</div></div>;

  return (
    <div className="adm-table-wrap">
      {products.map((p) => (
        <div key={p.id} className="adm-table-card" style={{ marginBottom: 16 }}>
          {/* Product header row */}
          <div
            className="adm-product-header"
            onClick={() => setExpanded((e) => ({ ...e, [p.id]: !e[p.id] }))}
          >
            <span className="adm-product-header__toggle">{expanded[p.id] ? '▾' : '▸'}</span>
            <strong className="adm-product-header__name">{p.name}</strong>
            <span className="adm-product-header__meta">{p.season}</span>
            <span className={`adm-badge adm-badge--${p.is_active ? 'confirmed' : 'cancelled'}`}>
              {p.is_active ? '上架中' : '已下架'}
            </span>
            <span className="adm-product-header__meta">{p.specs?.length ?? 0} 個規格</span>
          </div>

          {/* Spec rows */}
          {expanded[p.id] && (
            <table className="adm-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: 32 }}>規格名稱</th>
                  <th>容量</th>
                  <th className="adm-num">售價</th>
                  <th className="adm-num">庫存</th>
                  <th>庫存狀態</th>
                  <th>圖片數</th>
                  <th>狀態</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(p.specs || []).map((s) => (
                  <tr key={s.id}>
                    <td style={{ paddingLeft: 32 }}>{s.label}</td>
                    <td className="adm-muted">{s.qty_text}</td>
                    <td className="adm-num">NT$ {Number(s.price).toLocaleString()}</td>
                    <td className="adm-num">{s.stock_qty}</td>
                    <td>
                      <span className={`adm-badge adm-badge--${s.stock_status === 'in' ? 'confirmed' : s.stock_status === 'low' ? 'shipping' : 'cancelled'}`}>
                        {STOCK_STATUS_LABELS[s.stock_status] || s.stock_status}
                      </span>
                    </td>
                    <td>{s.images?.length ?? 0}</td>
                    <td>
                      <span className={`adm-badge adm-badge--${s.is_active ? 'confirmed' : 'cancelled'}`}>
                        {s.is_active ? '上架' : '下架'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="adm-btn adm-btn--secondary"
                        style={{ fontSize: 12 }}
                        onClick={() => setEditSpec(s)}
                      >
                        編輯規格
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}

      {editSpec && (
        <SpecEditModal
          spec={editSpec}
          token={token}
          onClose={() => setEditSpec(null)}
          onSaved={() => { setEditSpec(null); load(); }}
        />
      )}
    </div>
  );
}

/* ── Main app ── */
export default function AdminApp() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [admin, setAdmin] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [activeTab, setActiveTab] = useState('orders');

  const [filters, setFilters] = useState({
    status: '',
    searchText: '',
    date_from: '',
    date_to: '',
  });
  const [orders, setOrders] = useState({ total: 0, page: 1, page_size: 20, items: [] });
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState('');

  const [selectedOrderNo, setSelectedOrderNo] = useState('');
  const [modalOpen, setModalOpen] = useState(false);

  const initialLoadDone = useRef(false);
  const reqCountRef = useRef(0);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken('');
    setAdmin(null);
    setSelectedOrderNo('');
    setModalOpen(false);
  }, []);

  const loadOrders = useCallback(
    async (page = 1, overrideFilters) => {
      if (!token) return;
      const active = overrideFilters ?? filters;
      const reqId = ++reqCountRef.current;
      setListLoading(true);
      setListError('');
      try {
        const params = { ...resolveSearchParams(active), page, page_size: 20 };
        const data = await listAdminOrders(token, params);
        if (reqId === reqCountRef.current) setOrders(data);
      } catch (err) {
        if (reqId === reqCountRef.current) {
          if (err?.status === 401) logout();
          else setListError(err?.data?.detail || '無法載入訂單。');
        }
      } finally {
        if (reqId === reqCountRef.current) setListLoading(false);
      }
    },
    [token, filters, logout],
  );

  useEffect(() => {
    if (!token) { setAuthChecked(true); return; }
    getCurrentAdmin(token)
      .then((user) => { setAdmin(user); setAuthChecked(true); })
      .catch(() => { logout(); setAuthChecked(true); });
  }, [token, logout]);

  useEffect(() => {
    if (admin && !initialLoadDone.current) {
      initialLoadDone.current = true;
      loadOrders(1);
    }
  }, [admin, loadOrders]);

  const handleLogin = (accessToken) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
  };

  const openModal = useCallback((orderNo) => {
    setSelectedOrderNo(orderNo);
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => setModalOpen(false), []);

  if (!authChecked) return <div className="adm-loading">載入中…</div>;
  if (!token || !admin) return <LoginView onLogin={handleLogin} />;

  return (
    <div className="adm-shell">
      {/* Topbar */}
      <header className="adm-topbar">
        <span className="adm-topbar__logo">妙媽媽果園</span>
        <nav className="adm-topbar__nav">
          <button
            className={`adm-topbar__nav-item${activeTab === 'orders' ? ' adm-topbar__nav-item--active' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            訂單管理
          </button>
          <button
            className={`adm-topbar__nav-item${activeTab === 'products' ? ' adm-topbar__nav-item--active' : ''}`}
            onClick={() => setActiveTab('products')}
          >
            商品管理
          </button>
        </nav>
        <div className="adm-topbar__user">
          <span className="adm-topbar__username">{admin.username}</span>
          <button className="adm-btn adm-btn--ghost" onClick={logout}>登出</button>
        </div>
      </header>

      {/* Orders tab */}
      {activeTab === 'orders' && (
        <>
          <div className="adm-page-head">
            <h1 className="adm-page-head__title">訂單管理</h1>
            <span className="adm-page-head__count">共 {orders.total} 筆訂單</span>
          </div>
          <FilterStrip
            totalAll={orders.total}
            filters={filters}
            setFilters={setFilters}
            onSearch={(f) => loadOrders(1, f)}
          />
          <Alert message={listError} />
          <div className="adm-table-wrap">
            {listLoading ? (
              <div className="adm-table-card">
                <div className="adm-empty">載入訂單中…</div>
              </div>
            ) : (
              <OrdersTable
                orders={orders.items}
                selectedOrderNo={selectedOrderNo}
                onSelect={openModal}
              />
            )}
            {orders.total > 0 && (
              <div className="adm-pagination">
                <span>
                  第 {orders.page} 頁，共{' '}
                  {Math.ceil(orders.total / orders.page_size)} 頁
                </span>
                <div className="adm-pager">
                  <button
                    className="adm-pager-btn"
                    disabled={orders.page <= 1 || listLoading}
                    onClick={() => loadOrders(orders.page - 1)}
                  >
                    ← 上一頁
                  </button>
                  <div className="adm-pager-current">{orders.page}</div>
                  <button
                    className="adm-pager-btn"
                    disabled={orders.page * orders.page_size >= orders.total || listLoading}
                    onClick={() => loadOrders(orders.page + 1)}
                  >
                    下一頁 →
                  </button>
                </div>
              </div>
            )}
          </div>
          {modalOpen && selectedOrderNo && (
            <OrderModal
              orderNo={selectedOrderNo}
              token={token}
              onClose={closeModal}
              onStatusChange={() => loadOrders(orders.page)}
            />
          )}
        </>
      )}

      {/* Products tab */}
      {activeTab === 'products' && (
        <>
          <div className="adm-page-head">
            <h1 className="adm-page-head__title">商品管理</h1>
          </div>
          <ProductsTab token={token} />
        </>
      )}
    </div>
  );
}
