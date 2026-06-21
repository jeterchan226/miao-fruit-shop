# Admin UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 改寫後台管理介面，讓視覺風格與前台統一（白底 + 深 Sage 頂欄），版面改為全幅表格 + 置中 Modal 明細，篩選列改為 Chip 狀態切換 + 統一搜尋框。

**Architecture:** 僅改寫兩個檔案：`frontend/assets/admin.css`（全部樣式）與 `frontend/src/AdminApp.jsx`（元件邏輯 + markup）。`api.js`、`main.jsx`、`colors_and_type.css` 完全不動。沿用現有 API 合約與 token 邏輯。

**Tech Stack:** React 18, Vite 8, CSS（依賴 `colors_and_type.css` token），無獨立測試框架（以瀏覽器視覺驗證為主）。

**Spec:** `docs/superpowers/specs/2026-06-14-admin-ui-redesign.md`

---

## File Structure

改寫（不新增）：
- `frontend/assets/admin.css` — 全部改寫為新設計系統 CSS
- `frontend/src/AdminApp.jsx` — 全部改寫：LoginView、FilterStrip、OrdersTable、OrderModal、AdminApp

---

## Task 1: 改寫 admin.css

**Files:**
- Rewrite: `frontend/assets/admin.css`

- [x] **Step 1: 確認 dev server 可以啟動**

```bash
cd frontend && npm run dev
```

開啟 `http://localhost:8080/admin`，確認當前後台可以正常顯示（不論樣式如何）。確認後 Ctrl-C 停止。

- [x] **Step 2: 改寫 `frontend/assets/admin.css`**

以下為完整新版 CSS（全數取代舊檔內容）：

```css
/* Admin — redesigned 2026-06-14
   Depends on colors_and_type.css being loaded first.
*/

/* ── Reset ── */
button, input, select, textarea { font: inherit; }
button { cursor: pointer; }

/* ── Shell ── */
.adm-shell {
  min-height: 100vh;
  background: #F8F5F0;
  color: var(--brown-700);
  font-family: var(--font-sans-cjk);
}

/* ── Topbar ── */
.adm-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 24px;
  background: var(--sage-900);
}
.adm-topbar__logo {
  font-family: var(--font-serif-cjk);
  font-size: 16px;
  font-weight: 600;
  color: #E6EBD7;
  letter-spacing: -0.01em;
}
.adm-topbar__nav { display: flex; gap: 2px; }
.adm-topbar__nav-item {
  padding: 6px 14px;
  border-radius: var(--r-sm);
  font-size: 13px;
  color: var(--sage-300);
  cursor: pointer;
  transition: background var(--dur-micro);
  border: none;
  background: transparent;
}
.adm-topbar__nav-item:hover { background: rgba(255,255,255,.08); }
.adm-topbar__nav-item--active {
  color: #fff;
  background: rgba(255,255,255,.12);
  font-weight: 600;
}
.adm-topbar__user { display: flex; align-items: center; gap: 10px; }
.adm-topbar__username { font-size: 13px; color: var(--sage-300); }

/* ── Buttons ── */
.adm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 14px;
  border-radius: var(--r-sm);
  font-size: 13px;
  font-weight: 600;
  transition: all var(--dur-micro);
  white-space: nowrap;
}
.adm-btn--ghost {
  border: 1px solid rgba(255,255,255,.18);
  background: transparent;
  color: var(--sage-300);
}
.adm-btn--ghost:hover { border-color: rgba(255,255,255,.35); color: #E6EBD7; }
.adm-btn--secondary {
  border: 1px solid var(--sage-300);
  background: #fff;
  color: var(--brown-700);
}
.adm-btn--secondary:hover { border-color: var(--sage-600); }
.adm-btn--primary {
  border: none;
  background: var(--sage-900);
  color: var(--cream-card);
}
.adm-btn--primary:hover { background: var(--sage-700); }
.adm-btn:disabled { opacity: .45; cursor: not-allowed; }

/* ── Page header ── */
.adm-page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 20px 24px 0;
}
.adm-page-head__title {
  font-family: var(--font-serif-cjk);
  font-size: 22px;
  font-weight: 700;
  color: var(--brown-800);
  margin: 0;
}
.adm-page-head__count { font-size: 13px; color: var(--brown-500); padding-bottom: 2px; }

/* ── Alert ── */
.adm-alert {
  margin: 12px 24px 0;
  padding: 10px 14px;
  border: 1px solid rgba(194,74,58,.3);
  border-radius: var(--r-sm);
  background: rgba(194,74,58,.07);
  color: var(--packaging-red);
  font-size: 13px;
}

/* ── Filter strip ── */
.adm-filters {
  padding: 14px 24px 16px;
  border-bottom: 1px solid #E6EBD7;
}
.adm-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.adm-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  padding: 0 13px;
  border-radius: var(--r-pill);
  border: 1px solid var(--sage-200);
  background: #fff;
  font-size: 12px;
  color: var(--brown-700);
  cursor: pointer;
  transition: all var(--dur-micro);
  user-select: none;
}
.adm-chip:hover { border-color: var(--sage-500); color: var(--brown-800); }
.adm-chip--active {
  background: var(--sage-900);
  border-color: var(--sage-900);
  color: #fff;
  font-weight: 600;
}
.adm-chip__count {
  font-size: 10px;
  font-weight: 700;
  padding: 0 5px;
  border-radius: 8px;
  min-width: 18px;
  text-align: center;
  background: #EDE5D5;
  color: var(--brown-500);
}
.adm-chip--active .adm-chip__count {
  background: rgba(255,255,255,.2);
  color: rgba(255,255,255,.9);
}
.adm-search-row { display: flex; gap: 8px; align-items: center; }
.adm-search { position: relative; flex: 1; }
.adm-search__icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: var(--brown-500);
  pointer-events: none;
}
.adm-search__input {
  width: 100%;
  height: 34px;
  border: 1px solid var(--sage-200);
  border-radius: var(--r-sm);
  background: #fff;
  padding: 0 12px 0 32px;
  font-size: 13px;
  color: var(--brown-800);
  transition: border-color var(--dur-micro);
}
.adm-search__input:focus { outline: none; border-color: var(--sage-600); }
.adm-search__input::placeholder { color: #B8A89A; }
.adm-date-range { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.adm-date-input {
  width: 130px;
  height: 34px;
  border: 1px solid var(--sage-200);
  border-radius: var(--r-sm);
  background: #fff;
  padding: 0 10px;
  font-size: 12px;
  color: var(--brown-800);
  transition: border-color var(--dur-micro);
}
.adm-date-input:focus { outline: none; border-color: var(--sage-600); }
.adm-date-sep { font-size: 12px; color: var(--brown-500); }

/* ── Table ── */
.adm-table-wrap { padding: 16px 24px; }
.adm-table-card {
  background: #fff;
  border-radius: var(--r-md);
  box-shadow: var(--shadow-1), 0 2px 8px rgba(58,45,31,.04);
  overflow: hidden;
}
.adm-table { width: 100%; border-collapse: collapse; }
.adm-table thead th {
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--brown-500);
  letter-spacing: .06em;
  text-transform: uppercase;
  background: #fff;
  border-bottom: 2px solid #F0E8DA;
  white-space: nowrap;
}
.adm-table thead th.adm-num { text-align: right; }
.adm-table tbody td {
  padding: 12px 14px;
  font-size: 13px;
  color: var(--brown-700);
  border-bottom: 1px solid #F5EDE0;
  white-space: nowrap;
}
.adm-table tbody tr { cursor: pointer; transition: background var(--dur-micro); }
.adm-table tbody tr:hover td { background: #FAF5ED; }
.adm-table tbody tr.is-selected td { background: #F5EDE0; }
.adm-table tbody tr:last-child td { border-bottom: none; }
.adm-mono {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--sage-700);
  font-weight: 500;
}
.adm-num { text-align: right; font-variant-numeric: tabular-nums; }
.adm-muted { color: var(--brown-500); }

/* ── Status badge ── */
.adm-badge {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 9px;
  border-radius: 11px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  gap: 5px;
}
.adm-badge::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.adm-badge--pending_payment,
.adm-badge--pending     { background: #FFF3CD; color: #856404; }
.adm-badge--pending_payment::before,
.adm-badge--pending::before     { background: #D9923B; }
.adm-badge--confirmed   { background: #D1E7DD; color: #0f5132; }
.adm-badge--confirmed::before   { background: #198754; }
.adm-badge--shipping    { background: #CFE2FF; color: #084298; }
.adm-badge--shipping::before    { background: #0d6efd; }
.adm-badge--delivered   { background: #D1E7DD; color: #0f5132; }
.adm-badge--delivered::before   { background: var(--sage-600); }
.adm-badge--cancelled   { background: #F8D7DA; color: #842029; }
.adm-badge--cancelled::before   { background: var(--packaging-red); }

/* Badge (large) — same colour modifiers, different sizing */
.adm-badge-lg {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 11px;
  border-radius: 13px;
  font-size: 12px;
  font-weight: 600;
}
.adm-badge-lg::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── Empty / loading ── */
.adm-empty {
  padding: 40px;
  text-align: center;
  color: var(--brown-500);
  font-size: 14px;
}

/* ── Pagination ── */
.adm-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-top: 1px solid #F0E8DA;
  font-size: 13px;
  color: var(--brown-500);
}
.adm-pager { display: flex; align-items: center; gap: 8px; }
.adm-pager-btn {
  height: 30px;
  padding: 0 12px;
  border-radius: var(--r-sm);
  border: 1px solid var(--sage-200);
  background: #fff;
  font-size: 12px;
  color: var(--brown-700);
  transition: border-color var(--dur-micro);
}
.adm-pager-btn:hover:not(:disabled) { border-color: var(--sage-500); }
.adm-pager-btn:disabled { opacity: .4; cursor: not-allowed; }
.adm-pager-current {
  width: 30px;
  height: 30px;
  border-radius: var(--r-sm);
  background: var(--sage-900);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

/* ── Modal overlay ── */
.adm-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(30,22,14,.6);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.adm-modal {
  width: min(640px, 90vw);
  max-height: 85vh;
  background: #fff;
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Modal header */
.adm-modal__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #E6EBD7;
  background: #FDFAF4;
  flex-shrink: 0;
}
.adm-modal__order-no {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--sage-700);
  font-weight: 500;
  margin-bottom: 3px;
}
.adm-modal__customer { font-size: 18px; font-weight: 700; color: var(--brown-800); }
.adm-modal__head-right { display: flex; align-items: center; gap: 10px; }
.adm-modal__close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #F0E8DA;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--brown-500);
  transition: background var(--dur-micro);
}
.adm-modal__close:hover { background: #E5D8C5; color: var(--brown-800); }

/* Modal body */
.adm-modal__body {
  padding: 18px 20px;
  overflow-y: auto;
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
.adm-modal__section { margin-bottom: 18px; }
.adm-modal__section-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--brown-500);
  margin-bottom: 8px;
}
.adm-modal__dl {
  display: grid;
  grid-template-columns: 68px 1fr;
  gap: 5px 10px;
  font-size: 13px;
}
.adm-modal__dl dt { color: var(--brown-500); }
.adm-modal__dl dd { color: var(--brown-700); }
.adm-modal__items { display: flex; flex-direction: column; }
.adm-modal__item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px solid #F0E8DA;
  font-size: 13px;
}
.adm-modal__item:last-child { border-bottom: none; }
.adm-modal__item-name { color: var(--brown-800); font-weight: 500; }
.adm-modal__item-spec { color: var(--brown-500); font-size: 12px; margin-top: 1px; }
.adm-modal__item-price { color: var(--brown-700); font-weight: 600; white-space: nowrap; }
.adm-modal__totals {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 5px 12px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #E6EBD7;
  font-size: 12px;
  color: var(--brown-500);
}
.adm-modal__totals span:nth-child(even) { text-align: right; color: var(--brown-700); }
.adm-modal__totals .grand { color: var(--brown-800); font-size: 14px; font-weight: 700; }
.adm-modal__totals .grand-val {
  color: var(--brown-800);
  font-size: 14px;
  font-weight: 700;
  text-align: right;
}

/* Modal error */
.adm-modal__error {
  padding: 12px 20px 0;
  font-size: 13px;
  color: var(--packaging-red);
}

/* Modal footer */
.adm-modal__foot {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #E6EBD7;
  background: #FDFAF4;
  flex-shrink: 0;
}
.adm-modal__foot-label { font-size: 12px; color: var(--brown-500); flex-shrink: 0; }
.adm-modal__status-select {
  flex: 1;
  height: 34px;
  border: 1px solid var(--sage-200);
  border-radius: var(--r-sm);
  background: #fff;
  font-size: 13px;
  padding: 0 10px;
  color: var(--brown-800);
}
.adm-modal__status-select:focus { outline: none; border-color: var(--sage-600); }
.adm-modal__update-btn {
  height: 34px;
  padding: 0 18px;
  border-radius: var(--r-sm);
  border: none;
  background: var(--sage-900);
  color: var(--cream-card);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: background var(--dur-micro);
}
.adm-modal__update-btn:hover:not(:disabled) { background: var(--sage-700); }
.adm-modal__update-btn:disabled { opacity: .4; cursor: not-allowed; }

/* ── Login page ── */
.adm-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #F8F5F0;
}
.adm-login__box {
  width: min(400px, 100%);
  background: #fff;
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-2);
  overflow: hidden;
}
.adm-login__header {
  padding: 24px 28px 20px;
  background: var(--sage-900);
}
.adm-login__eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--sage-300);
  margin-bottom: 4px;
}
.adm-login__title {
  font-family: var(--font-serif-cjk);
  font-size: 20px;
  font-weight: 600;
  color: #E6EBD7;
  margin: 0;
}
.adm-login__form {
  padding: 24px 28px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.adm-login__label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--brown-500);
}
.adm-login__input {
  height: 38px;
  border: 1px solid var(--sage-200);
  border-radius: var(--r-sm);
  background: #F8F5F0;
  padding: 0 12px;
  font-size: 14px;
  color: var(--brown-800);
  transition: border-color var(--dur-micro);
}
.adm-login__input:focus { outline: none; border-color: var(--sage-600); background: #fff; }
.adm-login__submit {
  height: 40px;
  border: none;
  border-radius: var(--r-sm);
  background: var(--sage-900);
  color: var(--cream-card);
  font-size: 14px;
  font-weight: 600;
  margin-top: 4px;
  transition: background var(--dur-micro);
}
.adm-login__submit:hover:not(:disabled) { background: var(--sage-700); }
.adm-login__submit:disabled { opacity: .5; cursor: not-allowed; }

/* ── Loading centre ── */
.adm-loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--brown-500);
  font-size: 14px;
  background: #F8F5F0;
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .adm-modal__body { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .adm-topbar { padding: 0 14px; }
  .adm-topbar__nav { display: none; }
  .adm-table-wrap { padding: 10px 14px; }
  .adm-page-head { padding: 14px 14px 0; }
  .adm-filters { padding: 10px 14px 12px; }
  .adm-date-range { display: none; }
}
```

- [x] **Step 3: 啟動 dev server，驗證登入頁樣式**

```bash
cd frontend && npm run dev
```

開啟 `http://localhost:8080/admin`。

預期結果（目前 AdminApp.jsx 尚未改寫，class names 不吻合，登入頁基本可見即可）：
- 頁面不報 JS 錯誤
- 不需要完整樣式，Task 2 改完後才會對齊

若有 CSS syntax error，修正後繼續。

- [x] **Step 4: Commit**

```bash
git add frontend/assets/admin.css
git commit -m "style(admin): rewrite admin.css — new design system (sage topbar, modal, chips)"
```

---

## Task 2: 改寫 AdminApp.jsx

**Files:**
- Rewrite: `frontend/src/AdminApp.jsx`

- [x] **Step 1: 完整改寫 `frontend/src/AdminApp.jsx`**

以下為完整新版檔案內容（全數取代）：

```jsx
/* Admin order management — redesigned 2026-06-14 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  getAdminOrder,
  getCurrentAdmin,
  listAdminOrders,
  loginAdmin,
  updateAdminOrderStatus,
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

const money = (n) => `NT$ ${Number(n || 0).toLocaleString()}`;
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
    setLoading(true);
    setError('');
    setDetail(null);
    setStatusTarget('');
    setUpdateError('');
    getAdminOrder(token, orderNo)
      .then((data) => { setDetail(data); setLoading(false); })
      .catch(() => { setError('無法載入訂單明細。'); setLoading(false); });
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

/* ── Main app ── */
export default function AdminApp() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [admin, setAdmin] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

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
      setListLoading(true);
      setListError('');
      try {
        const params = { ...resolveSearchParams(active), page, page_size: 20 };
        const data = await listAdminOrders(token, params);
        setOrders(data);
      } catch (err) {
        if (err?.status === 401) logout();
        else setListError(err?.data?.detail || '無法載入訂單。');
      } finally {
        setListLoading(false);
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

  useEffect(() => { if (admin) loadOrders(1); }, [admin]);

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
          <button className="adm-topbar__nav-item adm-topbar__nav-item--active">
            訂單管理
          </button>
          <button className="adm-topbar__nav-item">商品管理</button>
        </nav>
        <div className="adm-topbar__user">
          <span className="adm-topbar__username">{admin.username}</span>
          <button className="adm-btn adm-btn--ghost" onClick={logout}>登出</button>
        </div>
      </header>

      {/* Page header */}
      <div className="adm-page-head">
        <h1 className="adm-page-head__title">訂單管理</h1>
        <span className="adm-page-head__count">共 {orders.total} 筆訂單</span>
      </div>

      {/* Filter */}
      <FilterStrip
        totalAll={orders.total}
        filters={filters}
        setFilters={setFilters}
        onSearch={(f) => loadOrders(1, f)}
      />

      {/* List error */}
      <Alert message={listError} />

      {/* Table + pagination */}
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
                disabled={orders.items.length < orders.page_size || listLoading}
                onClick={() => loadOrders(orders.page + 1)}
              >
                下一頁 →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && selectedOrderNo && (
        <OrderModal
          orderNo={selectedOrderNo}
          token={token}
          onClose={closeModal}
          onStatusChange={() => loadOrders(orders.page)}
        />
      )}
    </div>
  );
}
```

- [x] **Step 2: 確認 dev server 仍在執行，開啟後台**

若 dev server 已停止，重新啟動：

```bash
cd frontend && npm run dev
```

開啟 `http://localhost:8080/admin`。

- [x] **Step 3: 驗證登入頁**

預期結果：
- 頁面背景 `#F8F5F0` 淡米白
- 置中白色卡片，上方深 Sage `#4F5C3D` header 區塊
- header 內有小灰字「MIAO FRUIT SHOP」＋「後台管理」白色serif字
- 表單欄位：帳號 / 密碼，均有圓角 input
- 「登入」按鈕為深 Sage 綠
- 輸入錯誤帳號密碼（若後端未啟動），應看到紅色 error alert

- [x] **Step 4: 驗證登入後主頁面**

若後端已在 `localhost:8000` 執行，使用正確帳號登入。

預期結果：
- 頂欄：深 Sage `#4F5C3D`，左方 Noto Serif「妙媽媽果園」，中間「訂單管理」active nav，右方 username + 登出按鈕
- 頁面標題「訂單管理」(serif)，右方「共 N 筆訂單」
- Chip 列：全部/待付款/待確認/已確認/出貨中/已送達/已取消；預設「全部」為 active（深綠填色）
- 搜尋框有放大鏡 icon；日期區間兩個 input
- 表格：白底卡片 + 圓角，欄位 header 小寫灰字
- 訂單編號 IBM Plex Mono 綠字；狀態 badge 帶色點

- [x] **Step 5: 驗證 Modal**

點擊表格任意一列。

預期結果：
- 遮罩出現（深色模糊）
- 置中白色 Modal（最寬 640px）
- Header：左方訂單號（mono）+ 客戶名（大字）；右方狀態 badge + ✕ 按鈕
- Body 2 欄：左收件資訊 dl；右商品明細 + 小計/運費/手續費/總計
- Footer：「變更狀態」label + select + 「確認更新」按鈕
- 按 Escape 或點遮罩可關閉

- [x] **Step 6: 驗證狀態更新**

在 Modal footer，選擇一個合法的下一個狀態，點「確認更新」。

預期結果：
- 按鈕顯示「更新中…」並 disabled
- 成功後：Modal header 的狀態 badge 更新；表格列的 badge 也更新（重載後）
- 若選非法轉移（應在 select 中不可見，因為只顯示合法選項）

- [x] **Step 7: Commit**

```bash
git add frontend/src/AdminApp.jsx
git commit -m "feat(admin): rewrite AdminApp — chip filter, full-width table, centered modal"
```

---

## Definition of Done

- [x] `http://localhost:8080/admin` 登入頁符合新設計（白卡片 + 深 Sage header）
- [x] 登入後頂欄為深 Sage，含 Nav + 使用者資訊
- [x] Chip 篩選列可切換狀態，「全部」chip 顯示當前總筆數
- [x] 搜尋框輸入 300ms debounce 後觸發查詢；前綴 `MM-` 走 order_no，否則走 q
- [x] 日期起迄 input 改變後立即觸發查詢
- [x] 表格全幅，無側邊欄；列 hover 效果；選中列有 highlight
- [x] 點列 → Modal 出現；Escape / 點遮罩 / ✕ 均可關閉
- [x] Modal 雙欄：左收件資訊，右商品明細 + 金額總計
- [x] Modal footer 狀態 select 只顯示合法下一狀態；終態（delivered/cancelled）select disabled
- [x] 更新狀態成功後 Modal header badge 即時更新，表格重新載入
- [x] 401 回應 → 自動登出
- [x] `http://localhost:8080/` 前台商店頁面不受影響
