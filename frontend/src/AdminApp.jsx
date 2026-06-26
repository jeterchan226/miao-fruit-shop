/* Admin order management — redesigned 2026-06-14 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  DndContext,
  PointerSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import {
  createSpec,
  deleteProductImage,
  deleteSpec,
  getAdminOrder,
  getAdminOrderSummary,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listSpecImages,
  loginAdmin,
  registerSpecImage,
  reorderSpecImages,
  signUpload,
  updateAdminOrderStatus,
  updateSpec,
} from './api.js';

import { useOrderNotifications } from './useOrderNotifications.js';
import { formatRelativeTime } from './notifications.js';

const TOKEN_KEY = 'miao.admin.token';

const STATUS_LABELS = {
  pending_payment: '待付款',
  ready: '待出貨',
  shipping: '已出貨',
  cancelled: '已取消',
};

const NEXT_STATUS = {
  pending_payment: ['ready', 'cancelled'],
  ready: ['shipping', 'cancelled'],
  shipping: [],
  cancelled: [],
};

const CHIP_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'pending_payment', label: '待付款' },
  { value: 'ready', label: '待出貨' },
  { value: 'shipping', label: '已出貨' },
  { value: 'cancelled', label: '已取消' },
];

const DELIVERY_WINDOW_LABELS = {
  any: '不指定',
  am: '上午 9–13',
  pm: '下午 14–18',
};

const PAYMENT_METHOD_LABELS = {
  transfer: '銀行轉帳',
  // 以下為舊資料相容用,新訂單一律為 transfer。
  linepay: 'LINE Pay',
  card: '信用卡',
  atm: 'ATM 轉帳',
  cod: '貨到付款',
};

const LINE_FRIENDSHIP_LABELS = {
  friend: '已加入官方帳號',
  not_friend: '尚未加入官方帳號',
  unknown: '未確認',
};

const money = (n) => `NT$ ${Number(n || 0).toLocaleString()}`;
const dateText = (s) =>
  s ? new Date(s).toLocaleString('zh-TW', { hour12: false }) : '—';
const statusLabel = (s) => STATUS_LABELS[s] || '—';

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

/* ── Dashboard stat icons ── */
const STAT_ICON = {
  orders: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 4V3.2A1.2 1.2 0 0 1 10.2 2h3.6A1.2 1.2 0 0 1 15 3.2V4" />
      <path d="M8.5 10h7M8.5 14h7M8.5 18h4" />
    </svg>
  ),
  revenue: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2.5" y="6" width="19" height="13" rx="2.5" />
      <path d="M2.5 10.5h19" />
      <circle cx="17" cy="14.5" r="1.3" />
    </svg>
  ),
  pending: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2.5 6.5h10v9h-10z" />
      <path d="M12.5 9.5h4l3 3v3h-7z" />
      <circle cx="6" cy="17" r="1.8" />
      <circle cx="16.5" cy="17" r="1.8" />
    </svg>
  ),
};

/* ── Dashboard stat cards（訂單查詢上方的三個統計區塊）── */
function StatCards({ token, reloadSignal }) {
  const [summary, setSummary] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setFailed(false);
    getAdminOrderSummary(token)
      .then((data) => { if (!cancelled) setSummary(data); })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; };
  }, [token, reloadSignal]);

  const cards = [
    {
      key: 'orders', tone: 'sage', icon: STAT_ICON.orders, label: '總訂單',
      value: summary ? summary.total_orders.toLocaleString() : '—',
      unit: '筆', note: '累積至今',
    },
    {
      key: 'revenue', tone: 'orange', icon: STAT_ICON.revenue, label: '總營收',
      prefix: 'NT$',
      value: summary ? summary.total_revenue.toLocaleString() : '—',
      note: '已完成訂單（不含取消）',
    },
    {
      key: 'pending', tone: 'red', icon: STAT_ICON.pending, label: '待出貨',
      value: summary ? summary.pending_shipment.toLocaleString() : '—',
      unit: '筆', note: '待安排出貨',
    },
  ];

  return (
    <div className="adm-stats">
      {cards.map((c) => (
        <div key={c.key} className={`adm-stat adm-stat--${c.tone}`}>
          <svg className="adm-stat__leaf" viewBox="0 0 48 48" aria-hidden="true">
            <path d="M40 8C20 8 8 20 8 40c20 0 32-12 32-32Z" fill="currentColor" />
            <path d="M14 34 34 14" stroke="#fff" strokeWidth="1.4" fill="none" opacity=".5" />
          </svg>
          <div className="adm-stat__head">
            <span className="adm-stat__icon">{c.icon}</span>
            <span className="adm-stat__label">{c.label}</span>
          </div>
          <div className="adm-stat__value">
            {c.prefix && <span className="adm-stat__prefix">{c.prefix}</span>}
            <span className="adm-stat__num">{c.value}</span>
            {c.unit && <span className="adm-stat__unit">{c.unit}</span>}
          </div>
          <div className="adm-stat__note">
            {failed ? '資料載入失敗' : c.note}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Filter strip ── */
function FilterStrip({ statusCounts, filters, setFilters, onSearch }) {
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
        {CHIP_OPTIONS.map(({ value, label }) => {
          const grandTotal = Object.values(statusCounts).reduce((a, b) => a + b, 0);
          const count = value === '' ? grandTotal : (statusCounts?.[value] ?? 0);
          return (
            <button
              key={value}
              className={`adm-chip${filters.status === value ? ' adm-chip--active' : ''}`}
              onClick={() => setChipStatus(value)}
            >
              {label}
              <span className="adm-chip__count">{count}</span>
            </button>
          );
        })}
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
      <table className="adm-table adm-table--orders">
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
                  <dt>LINE 通知</dt>
                  <dd>
                    <div className="adm-line">
                      {detail.line_picture_url && (
                        <img className="adm-line__avatar" src={detail.line_picture_url} alt="" />
                      )}
                      <div>
                        <div className="adm-line__name">
                          {detail.line_display_name || '—'}
                        </div>
                        <div className="adm-line__meta">
                          {detail.line_notification_consent ? '已同意通知' : '未同意通知'}
                          {' · '}
                          {LINE_FRIENDSHIP_LABELS[detail.line_friendship_status] || '未確認'}
                        </div>
                        {detail.line_user_id && (
                          <div className="adm-line__id">{detail.line_user_id}</div>
                        )}
                      </div>
                    </div>
                  </dd>
                  <dt>地址</dt>
                  <dd>
                    {detail.ship_zipcode}&nbsp;
                    {detail.ship_city}{detail.ship_district}{detail.ship_street}
                  </dd>
                  <dt>希望送達</dt><dd>{detail.preferred_date}</dd>
                  <dt>配送時段</dt><dd>{DELIVERY_WINDOW_LABELS[detail.delivery_window] || detail.delivery_window}</dd>
                  <dt>付款方式</dt><dd>{PAYMENT_METHOD_LABELS[detail.payment_method] || detail.payment_method}</dd>
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

const STOCK_STATUS_LABELS = { in: '現貨供應', low: '剩量不多', out: '已售完' };
const STOCK_STATUS_OPTIONS = [
  { value: 'in', label: '現貨供應' },
  { value: 'low', label: '剩量不多' },
  { value: 'out', label: '已售完' },
];

/* ── Sortable image item ── */
function SortableImageItem({ image, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: image.id });
  const style = { transform: CSS.Transform.toString(transform), transition };
  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`img-gallery__item${isDragging ? ' img-gallery__item--dragging' : ''}`}
    >
      <span className="img-gallery__drag-handle" {...attributes} {...listeners}>⠿</span>
      <img src={image.url} alt="" className="img-gallery__thumb" />
      <button
        className="img-gallery__delete"
        onClick={() => onDelete(image.id)}
        title="移除"
      >✕</button>
    </div>
  );
}

/* ── Spec image gallery (規格層級) ── */
function SpecImageGallery({ specId, token }) {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } }),
  );

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

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = images.findIndex((i) => i.id === active.id);
    const newIndex = images.findIndex((i) => i.id === over.id);
    setError('');
    const prevImages = images;
    const newImages = arrayMove(images, oldIndex, newIndex);
    setImages(newImages);
    try {
      await reorderSpecImages(
        token,
        specId,
        newImages.map((img, idx) => ({ id: img.id, sort_order: idx })),
      );
    } catch {
      setImages(prevImages);
      setError('排序儲存失敗，請稍後再試');
    }
  };

  return (
    <div className="img-gallery">
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={images.map((i) => i.id)} strategy={rectSortingStrategy}>
          <div className="img-gallery__grid">
            {images.map((img) => (
              <SortableImageItem key={img.id} image={img} onDelete={handleDelete} />
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
        </SortableContext>
      </DndContext>
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

const EMPTY_SPEC_FORM = {
  label: '', qty_text: '', price: '', stock_qty: '', note: '', low_stock_threshold: 3,
};

/* ── Create spec modal ── */
function CreateSpecModal({ productId, token, onClose, onCreated }) {
  const [form, setForm] = useState(EMPTY_SPEC_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  // After the spec exists we can attach images (needs a spec id), so switch the
  // modal into a second phase showing the same gallery as the edit modal.
  const [createdSpec, setCreatedSpec] = useState(null);

  // Once a spec has been created, any close must refresh the parent list.
  const close = createdSpec ? onCreated : onClose;

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [close]);

  const setField = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const handleCreate = async () => {
    if (!form.label || !form.qty_text || form.price === '' || form.stock_qty === '') {
      setError('請填寫所有必填欄位');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const spec = await createSpec(token, productId, {
        label: form.label,
        qty_text: form.qty_text,
        price: Number(form.price),
        stock_qty: Number(form.stock_qty),
        low_stock_threshold: Number(form.low_stock_threshold),
        note: form.note || null,
      });
      setCreatedSpec(spec);
      setSaving(false);
    } catch (err) {
      setError(err?.data?.detail || '新增失敗');
      setSaving(false);
    }
  };

  if (createdSpec) {
    return (
      <div className="adm-modal-overlay" onClick={onCreated}>
        <div className="adm-modal adm-modal--product" onClick={(e) => e.stopPropagation()}>
          <div className="adm-modal__head">
            <div>
              <div className="adm-modal__order-no">{createdSpec.label}</div>
              <div className="adm-modal__customer">規格已建立，可上傳圖片</div>
            </div>
            <button className="adm-modal__close" onClick={onCreated}>✕</button>
          </div>
          <div className="adm-modal__product-body">
            <div className="adm-modal__section">
              <div className="adm-modal__section-title">規格圖片</div>
              <SpecImageGallery specId={createdSpec.id} token={token} />
            </div>
          </div>
          <div className="adm-modal__foot">
            <span />
            <span />
            <button className="adm-modal__update-btn" onClick={onCreated}>完成</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="adm-modal-overlay" onClick={onClose}>
      <div className="adm-modal adm-modal--product" onClick={(e) => e.stopPropagation()}>
        <div className="adm-modal__head">
          <div className="adm-modal__order-no">新增規格</div>
          <button className="adm-modal__close" onClick={onClose}>✕</button>
        </div>
        <div className="adm-modal__product-body">
          <div className="adm-modal__section">
            <div className="adm-spec-form">
              <label className="adm-field">
                <span className="adm-field__label">規格名稱 *</span>
                <input className="adm-field__input" value={form.label}
                  onChange={(e) => setField('label', e.target.value)} placeholder="如：5 台斤家庭箱" />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">容量說明 *</span>
                <input className="adm-field__input" value={form.qty_text}
                  onChange={(e) => setField('qty_text', e.target.value)} placeholder="如：6–8 顆 · 5 台斤" />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">售價（NT$）*</span>
                <input className="adm-field__input" type="number" min="0" value={form.price}
                  onChange={(e) => setField('price', e.target.value)} />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">庫存數量 *</span>
                <input className="adm-field__input" type="number" min="0" value={form.stock_qty}
                  onChange={(e) => setField('stock_qty', e.target.value)} />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">低庫存警示（預設 3）</span>
                <input className="adm-field__input" type="number" min="0" value={form.low_stock_threshold}
                  onChange={(e) => setField('low_stock_threshold', e.target.value)} />
              </label>
              <label className="adm-field">
                <span className="adm-field__label">備註</span>
                <input className="adm-field__input" value={form.note}
                  onChange={(e) => setField('note', e.target.value)} placeholder="如：剩 3 箱" />
              </label>
            </div>
          </div>
          {error && <div className="adm-alert">{error}</div>}
        </div>
        <div className="adm-modal__foot">
          <span />
          <button className="adm-btn adm-btn--ghost" onClick={onClose}>取消</button>
          <button className="adm-modal__update-btn" onClick={handleCreate} disabled={saving}>
            {saving ? '新增中…' : '新增並上傳圖片'}
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
  const [createForProduct, setCreateForProduct] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [expanded, setExpanded] = useState({});

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listAdminProducts(token);
      setProducts(data);
      setExpanded((prev) => {
        const exp = { ...prev };
        data.forEach((p) => { if (exp[p.id] === undefined) exp[p.id] = true; });
        return exp;
      });
    } catch {
      setError('無法載入商品資料');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [token]);

  const moveSpec = async (specs, idx, direction) => {
    const targetIdx = idx + direction;
    if (targetIdx < 0 || targetIdx >= specs.length) return;
    const a = specs[idx], b = specs[targetIdx];
    const newOrderA = b.sort_order !== a.sort_order ? b.sort_order : b.sort_order + direction;
    await Promise.all([
      updateSpec(token, a.id, { sort_order: newOrderA }),
      updateSpec(token, b.id, { sort_order: a.sort_order }),
    ]);
    load();
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await deleteSpec(token, confirmDelete.id);
      setConfirmDelete(null);
      load();
    } catch (err) {
      alert(err?.data?.detail || '刪除失敗');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <div className="adm-table-wrap"><div className="adm-empty">載入商品中…</div></div>;
  if (error) return <div className="adm-table-wrap"><div className="adm-alert">{error}</div></div>;

  return (
    <div className="adm-table-wrap">
      {products.map((p) => (
        <div key={p.id} className="adm-table-card" style={{ marginBottom: 16 }}>
          {/* Product header */}
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
            <>
              <div className="adm-spec-scroll">
              <table className="adm-table adm-table--specs">
                <thead>
                  <tr>
                    <th style={{ width: 56 }}>順序</th>
                    <th>規格名稱</th>
                    <th>容量</th>
                    <th className="adm-num">售價</th>
                    <th className="adm-num">庫存</th>
                    <th>庫存狀態</th>
                    <th>圖片</th>
                    <th>狀態</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {(p.specs || []).map((s, idx, arr) => (
                    <tr key={s.id}>
                      <td>
                        <div className="adm-order-btns">
                          <button
                            className="adm-order-btn"
                            disabled={idx === 0}
                            onClick={() => moveSpec(arr, idx, -1)}
                            title="往上移"
                          >▲</button>
                          <button
                            className="adm-order-btn"
                            disabled={idx === arr.length - 1}
                            onClick={() => moveSpec(arr, idx, 1)}
                            title="往下移"
                          >▼</button>
                        </div>
                      </td>
                      <td>{s.label}</td>
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
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            className="adm-btn adm-btn--secondary"
                            style={{ fontSize: 13.5 }}
                            onClick={() => setEditSpec(s)}
                          >編輯</button>
                          <button
                            className="adm-btn adm-btn--danger"
                            style={{ fontSize: 13.5 }}
                            onClick={() => setConfirmDelete(s)}
                          >刪除</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
              <div style={{ padding: '10px 16px' }}>
                <button
                  className="adm-btn adm-btn--secondary"
                  style={{ fontSize: 14 }}
                  onClick={() => setCreateForProduct(p)}
                >＋ 新增規格</button>
              </div>
            </>
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

      {createForProduct && (
        <CreateSpecModal
          productId={createForProduct.id}
          token={token}
          onClose={() => setCreateForProduct(null)}
          onCreated={() => { setCreateForProduct(null); load(); }}
        />
      )}

      {confirmDelete && (
        <div className="adm-modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="adm-modal adm-modal--confirm" onClick={(e) => e.stopPropagation()}>
            <div className="adm-modal__head">
              <div className="adm-modal__order-no">確認刪除</div>
            </div>
            <div style={{ padding: '20px 24px' }}>
              <p>確定要永久刪除規格「<strong>{confirmDelete.label}</strong>」嗎？</p>
              <p style={{ fontSize: 13, color: 'var(--packaging-red)', marginTop: 8 }}>
                此操作無法復原，相關圖片將一併刪除。
              </p>
            </div>
            <div className="adm-modal__foot">
              <span />
              <button className="adm-btn adm-btn--ghost" onClick={() => setConfirmDelete(null)}>取消</button>
              <button className="adm-btn adm-btn--danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? '刪除中…' : '確認刪除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── 通知圖示 ── */
const BellIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);

const EyeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

function NotifPanel({ notif, onOpenOrder, onClose }) {
  const unreadSet = new Set(notif.unread.map((o) => o.order_no));
  return (
    <>
      <div className="adm-notif__backdrop" onClick={onClose} />
      <div className="adm-notif__panel" role="menu">
        <div className="adm-notif__head">
          <span>未讀通知</span>
          <div className="adm-notif__head-actions">
            <button className="adm-notif__sound" onClick={notif.toggleSound}>
              {notif.soundOn ? '🔔 音效開' : '🔕 音效關'}
            </button>
            {notif.unreadCount > 0 && (
              <button className="adm-notif__readall" onClick={notif.markAllRead}>
                全部標示已讀
              </button>
            )}
          </div>
        </div>
        {notif.recentOrders.length === 0 ? (
          <div className="adm-notif__empty">目前沒有訂單</div>
        ) : (
          <ul className="adm-notif__list">
            {notif.recentOrders.map((o) => (
              <li
                key={o.order_no}
                className={`adm-notif__item${unreadSet.has(o.order_no) ? ' adm-notif__item--unread' : ''}`}
                onClick={() => onOpenOrder(o)}
              >
                <div className="adm-notif__item-top">新訂單 {o.order_no}</div>
                <div className="adm-notif__item-sub">
                  {o.customer_name}・NT$ {o.total.toLocaleString()}・
                  {formatRelativeTime(o.created_at)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
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
  const [summaryKey, setSummaryKey] = useState(0);

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

  const [notifOpen, setNotifOpen] = useState(false);
  const notif = useOrderNotifications({ token, onAuthError: logout });

  const openOrderFromNotif = useCallback(
    (order) => {
      notif.markRead(order);
      setNotifOpen(false);
      setActiveTab('orders');
      openModal(order.order_no);
    },
    [notif, openModal],
  );

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
          <a
            className="adm-btn adm-btn--ghost adm-topbar__store"
            href="/"
            target="_blank"
            rel="noopener noreferrer"
          >
            <EyeIcon /> 查看前台
          </a>
          <div className="adm-notif">
            <button
              className="adm-notif__bell"
              aria-label="通知"
              onClick={() => {
                notif.unlockAudio();
                setNotifOpen((o) => !o);
              }}
            >
              <BellIcon />
              {notif.unreadCount > 0 && (
                <span className="adm-notif__badge">{notif.unreadCount}</span>
              )}
            </button>
            {notifOpen && (
              <NotifPanel
                notif={notif}
                onOpenOrder={openOrderFromNotif}
                onClose={() => setNotifOpen(false)}
              />
            )}
          </div>
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
          <StatCards token={token} reloadSignal={summaryKey} />
          <FilterStrip
            statusCounts={orders.status_counts || {}}
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

      {/* 訂單明細 modal：移到 shell 層，讓任一分頁 / 通知點擊都能開啟 */}
      {modalOpen && selectedOrderNo && (
        <OrderModal
          orderNo={selectedOrderNo}
          token={token}
          onClose={closeModal}
          onStatusChange={() => {
            loadOrders(orders.page);
            setSummaryKey((k) => k + 1);
            notif.refresh();
          }}
        />
      )}
    </div>
  );
}
