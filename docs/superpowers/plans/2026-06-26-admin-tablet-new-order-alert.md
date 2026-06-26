# 店內平板後台「新訂單即時提醒」Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 店內平板開著訂單後台時，新訂單以 header 鈴鐺未讀數 + 提示音即時通知店家，並可點通知直接看訂單；另加「查看前台」按鈕。

**Architecture:** 純前端，後端零改動。AdminApp 外層用 `useOrderNotifications` hook 每 ~20 秒輪詢既有 `GET /api/admin/orders?page=1&page_size=10`（本來就 `created_at desc`），以 `localStorage` 標記「已讀到的最新訂單時間」算未讀；新單觸發 WebAudio 提示音；header 加鈴鐺下拉與「查看前台」按鈕；以 Wake Lock 防螢幕睡眠。可單元測試的純邏輯抽到 `notifications.js`，用 Vitest 測；UI / 音效 / Wake Lock 等副作用以瀏覽器手動驗證。

**Tech Stack:** React 18、Vite 8、react-router-dom 7（既有）；新增 dev 依賴 Vitest。WebAudio API、Screen Wake Lock API、localStorage。

## Global Constraints

- 後端、資料庫 schema、既有客戶通知流程**不得變更**。
- 不新增 Web Push / Service Worker / PWA / 背景通知 / LINE 群組推播 / 出單印表機。
- 通知範圍僅「新訂單」（不含付款已確認等狀態）。
- 一切回覆與 UI 文案使用繁體中文（zh-TW）。
- 既有前端零測試慣例：本功能只對 `notifications.js` 純邏輯加 Vitest 單元測試，UI / 副作用手動驗證。
- 前端 helper 既有命名：列表 API 為 `listAdminOrders(token, filters)`；token localStorage key 為 `TOKEN_KEY`；訂單明細以 `openModal(orderNo)` 開啟。
- 訂單列表項欄位：`order_no`、`status`、`customer_name`、`customer_phone`、`total`、`created_at`。

---

## File Structure

**新增：**
- `frontend/src/notifications.js` — 純邏輯：相對時間、未讀計算、新單偵測。無 DOM / 無 localStorage / 無副作用。
- `frontend/src/notifications.test.js` — 上述純邏輯的 Vitest 測試。
- `frontend/src/chime.js` — WebAudio 提示音（`createChime()` → `{ unlock, play }`），無外部音檔。
- `frontend/src/useOrderNotifications.js` — 通知中心 hook：輪詢、未讀標記、提示音觸發、Wake Lock。

**修改：**
- `frontend/package.json` — 加 `vitest` dev 依賴與 `test` script。
- `frontend/src/AdminApp.jsx` — header 加鈴鐺下拉與「查看前台」；接 hook；OrderModal 移到 shell 層。
- `frontend/assets/admin.css` — 鈴鐺 / 徽章 / 下拉面板 / 未讀highlight / 查看前台按鈕樣式。

---

## Task 1: Vitest 設定 + 通知純邏輯（含測試）

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/notifications.js`
- Test: `frontend/src/notifications.test.js`

**Interfaces:**
- Consumes: 無。
- Produces:
  - `formatRelativeTime(iso: string, nowMs?: number) => string`（「剛剛」/「N 分鐘前」/「N 小時前」/「N 天前」）
  - `isAfter(aIso: string|null, bIso: string|null) => boolean`（a 嚴格晚於 b；任一為空回 false）
  - `newestCreatedAt(orders: {created_at:string}[]) => string|null`
  - `unreadOrders(orders: {created_at:string}[], lastReadAtIso: string|null) => orders[]`（晚於標記者；無標記回 `[]`）

- [ ] **Step 1: 加 Vitest dev 依賴與 test script**

於 `frontend/` 執行：

```bash
cd frontend && npm install -D vitest
```

然後在 `frontend/package.json` 的 `"scripts"` 區塊加入 `test`（保留既有 dev/build/preview）：

```json
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 8080",
    "build": "vite build",
    "preview": "vite preview --host 0.0.0.0 --port 8080",
    "test": "vitest run"
  },
```

- [ ] **Step 2: 寫失敗測試 `frontend/src/notifications.test.js`**

```js
import { describe, it, expect } from 'vitest';
import {
  formatRelativeTime,
  isAfter,
  newestCreatedAt,
  unreadOrders,
} from './notifications.js';

const NOW = Date.parse('2026-06-26T12:00:00Z');
const ago = (ms) => new Date(NOW - ms).toISOString();

describe('formatRelativeTime', () => {
  it('小於一分鐘 → 剛剛', () => {
    expect(formatRelativeTime(ago(30 * 1000), NOW)).toBe('剛剛');
  });
  it('分鐘', () => {
    expect(formatRelativeTime(ago(5 * 60 * 1000), NOW)).toBe('5 分鐘前');
  });
  it('小時', () => {
    expect(formatRelativeTime(ago(3 * 60 * 60 * 1000), NOW)).toBe('3 小時前');
  });
  it('天', () => {
    expect(formatRelativeTime(ago(2 * 24 * 60 * 60 * 1000), NOW)).toBe('2 天前');
  });
});

describe('isAfter', () => {
  it('a 晚於 b → true', () => {
    expect(isAfter(ago(0), ago(1000))).toBe(true);
  });
  it('a 不晚於 b → false', () => {
    expect(isAfter(ago(1000), ago(0))).toBe(false);
  });
  it('任一為空 → false', () => {
    expect(isAfter(null, ago(0))).toBe(false);
    expect(isAfter(ago(0), null)).toBe(false);
  });
});

describe('newestCreatedAt', () => {
  it('空陣列 → null', () => {
    expect(newestCreatedAt([])).toBe(null);
  });
  it('取最大 created_at', () => {
    const orders = [
      { created_at: ago(5000) },
      { created_at: ago(1000) },
      { created_at: ago(9000) },
    ];
    expect(newestCreatedAt(orders)).toBe(ago(1000));
  });
});

describe('unreadOrders', () => {
  it('無標記 → []', () => {
    expect(unreadOrders([{ created_at: ago(0) }], null)).toEqual([]);
  });
  it('回傳晚於標記者', () => {
    const marker = ago(5000);
    const orders = [
      { order_no: 'A', created_at: ago(1000) },
      { order_no: 'B', created_at: ago(9000) },
    ];
    expect(unreadOrders(orders, marker).map((o) => o.order_no)).toEqual(['A']);
  });
});
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `cd frontend && npm test`
Expected: FAIL（`Failed to resolve import './notifications.js'` 或函式未定義）

- [ ] **Step 4: 實作 `frontend/src/notifications.js`**

```js
// 純邏輯：通知中心的相對時間、未讀計算、新單偵測。
// 無 DOM、無 localStorage、無副作用，便於單元測試。

export function formatRelativeTime(iso, nowMs = Date.now()) {
  const then = new Date(iso).getTime();
  const diffSec = Math.max(0, Math.floor((nowMs - then) / 1000));
  if (diffSec < 60) return '剛剛';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} 分鐘前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小時前`;
  const diffDay = Math.floor(diffHour / 24);
  return `${diffDay} 天前`;
}

export function isAfter(aIso, bIso) {
  if (!aIso || !bIso) return false;
  return new Date(aIso).getTime() > new Date(bIso).getTime();
}

export function newestCreatedAt(orders) {
  if (!orders || orders.length === 0) return null;
  return orders.reduce(
    (max, o) =>
      max === null || new Date(o.created_at).getTime() > new Date(max).getTime()
        ? o.created_at
        : max,
    null,
  );
}

export function unreadOrders(orders, lastReadAtIso) {
  if (!orders || !lastReadAtIso) return [];
  return orders.filter((o) => isAfter(o.created_at, lastReadAtIso));
}
```

- [ ] **Step 5: 跑測試確認通過**

Run: `cd frontend && npm test`
Expected: PASS（4 個 describe 全綠）

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/notifications.js frontend/src/notifications.test.js
git commit -m "test(admin): 加 Vitest 與通知中心純邏輯(相對時間/未讀/新單偵測)"
```

---

## Task 2: 提示音 + 通知中心 hook

**Files:**
- Create: `frontend/src/chime.js`
- Create: `frontend/src/useOrderNotifications.js`

**Interfaces:**
- Consumes: `listAdminOrders(token, {page, page_size})`（`./api.js`）；`newestCreatedAt`、`unreadOrders`、`isAfter`（`./notifications.js`）。
- Produces:
  - `createChime() => { unlock(): void, play(): void }`
  - `useOrderNotifications({ token: string, onAuthError?: () => void }) => {`
    `recentOrders: order[], unread: order[], unreadCount: number,`
    `soundOn: boolean, toggleSound(): void, unlockAudio(): void,`
    `markRead(order): void, markAllRead(): void, refresh(): Promise<void> }`

> 本任務為副作用密集（音效、計時器、Wake Lock、localStorage），依專案決策**不寫單元測試**，以 `npm run build` 確認可編譯，最終於 Task 3 一併瀏覽器驗證。

- [ ] **Step 1: 建立 `frontend/src/chime.js`**

```js
// WebAudio 提示音；需在使用者手勢中先呼叫 unlock()。無外部音檔。
export function createChime() {
  let ctx = null;

  function ensureCtx() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    return ctx;
  }

  return {
    unlock() {
      const c = ensureCtx();
      if (c && c.state === 'suspended') c.resume();
    },
    play() {
      const c = ensureCtx();
      if (!c) return;
      if (c.state === 'suspended') c.resume();
      try {
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, c.currentTime);
        gain.gain.setValueAtTime(0.001, c.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.3, c.currentTime + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.35);
        osc.connect(gain).connect(c.destination);
        osc.start();
        osc.stop(c.currentTime + 0.36);
      } catch {
        /* 忽略播放失敗 */
      }
    },
  };
}
```

- [ ] **Step 2: 建立 `frontend/src/useOrderNotifications.js`**

```js
import { useCallback, useEffect, useRef, useState } from 'react';
import { listAdminOrders } from './api.js';
import { createChime } from './chime.js';
import { isAfter, newestCreatedAt, unreadOrders } from './notifications.js';

const LAST_READ_KEY = 'admin_notif_last_read_at';
const SOUND_KEY = 'admin_notif_sound_on';
const POLL_MS = 20000;
const RECENT_SIZE = 10;

export function useOrderNotifications({ token, onAuthError }) {
  const [recentOrders, setRecentOrders] = useState([]);
  const [lastReadAt, setLastReadAt] = useState(
    () => localStorage.getItem(LAST_READ_KEY) || null,
  );
  const [soundOn, setSoundOn] = useState(
    () => localStorage.getItem(SOUND_KEY) !== 'off',
  );

  const chimeRef = useRef(null);
  if (chimeRef.current === null) chimeRef.current = createChime();
  const prevNewestRef = useRef(null);
  const soundOnRef = useRef(soundOn);
  const unlockedRef = useRef(false);

  useEffect(() => {
    soundOnRef.current = soundOn;
  }, [soundOn]);

  const persistLastRead = useCallback((iso) => {
    if (!iso) return;
    setLastReadAt(iso);
    localStorage.setItem(LAST_READ_KEY, iso);
  }, []);

  const poll = useCallback(async () => {
    if (!token) return;
    let data;
    try {
      data = await listAdminOrders(token, { page: 1, page_size: RECENT_SIZE });
    } catch (err) {
      if (err?.status === 401) onAuthError?.();
      return;
    }
    const items = data.items || [];
    setRecentOrders(items);
    const newest = newestCreatedAt(items);

    // 首次：以最新訂單初始化基準，不發聲；無標記時順便初始化已讀標記。
    if (prevNewestRef.current === null) {
      prevNewestRef.current = newest;
      if (!localStorage.getItem(LAST_READ_KEY) && newest) persistLastRead(newest);
      return;
    }
    // 出現更新的訂單 → 發聲（需已解鎖音訊且開啟）。
    if (isAfter(newest, prevNewestRef.current)) {
      if (unlockedRef.current && soundOnRef.current) chimeRef.current.play();
    }
    prevNewestRef.current = newest;
  }, [token, onAuthError, persistLastRead]);

  // 輪詢：立即一次 + 每 POLL_MS。
  useEffect(() => {
    if (!token) return undefined;
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [token, poll]);

  // Wake Lock：前景時保持螢幕不睡，回前景時重新取得。
  useEffect(() => {
    if (!token) return undefined;
    let wakeLock = null;
    const request = async () => {
      try {
        if ('wakeLock' in navigator && document.visibilityState === 'visible') {
          wakeLock = await navigator.wakeLock.request('screen');
        }
      } catch {
        /* 不支援或被拒則略過 */
      }
    };
    const onVis = () => {
      if (document.visibilityState === 'visible') request();
    };
    request();
    document.addEventListener('visibilitychange', onVis);
    return () => {
      document.removeEventListener('visibilitychange', onVis);
      if (wakeLock) wakeLock.release().catch(() => {});
    };
  }, [token]);

  const unlockAudio = useCallback(() => {
    unlockedRef.current = true;
    chimeRef.current.unlock();
  }, []);

  const toggleSound = useCallback(() => {
    setSoundOn((on) => {
      const next = !on;
      localStorage.setItem(SOUND_KEY, next ? 'on' : 'off');
      return next;
    });
  }, []);

  const markRead = useCallback(
    (order) => {
      if (order?.created_at && isAfter(order.created_at, lastReadAt)) {
        persistLastRead(order.created_at);
      }
    },
    [lastReadAt, persistLastRead],
  );

  const markAllRead = useCallback(() => {
    const newest = newestCreatedAt(recentOrders);
    if (newest) persistLastRead(newest);
  }, [recentOrders, persistLastRead]);

  const unread = unreadOrders(recentOrders, lastReadAt);

  return {
    recentOrders,
    unread,
    unreadCount: unread.length,
    soundOn,
    toggleSound,
    unlockAudio,
    markRead,
    markAllRead,
    refresh: poll,
  };
}
```

- [ ] **Step 3: 確認可編譯**

Run: `cd frontend && npm run build`
Expected: 建置成功（無 import / 語法錯誤）

- [ ] **Step 4: Commit**

```bash
git add frontend/src/chime.js frontend/src/useOrderNotifications.js
git commit -m "feat(admin): 通知中心 hook(輪詢/未讀標記/提示音/Wake Lock)"
```

---

## Task 3: Header 鈴鐺下拉 + 查看前台 + 接線

**Files:**
- Modify: `frontend/src/AdminApp.jsx`
- Modify: `frontend/assets/admin.css`

**Interfaces:**
- Consumes: `useOrderNotifications`（`./useOrderNotifications.js`）、`formatRelativeTime`（`./notifications.js`）、既有 `openModal`、`logout`、`loadOrders`、`setActiveTab`、`OrderModal`。
- Produces: 無（終端 UI）。

> UI / 副作用，依決策不寫單元測試；以 `npm run build` + 瀏覽器手動驗證。

- [ ] **Step 1: 於 `AdminApp.jsx` 頂部 import 區加入**

在現有 `import` 群組末端加：

```js
import { useOrderNotifications } from './useOrderNotifications.js';
import { formatRelativeTime } from './notifications.js';
```

- [ ] **Step 2: 在 `AdminApp.jsx` `export default function AdminApp()` 之前，新增圖示與通知面板元件**

```jsx
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
```

- [ ] **Step 3: 在 `AdminApp()` 內接 hook 與狀態**

於 `const closeModal = useCallback(...)` 之後加入：

```jsx
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
```

- [ ] **Step 4: 改寫 topbar 的 `adm-topbar__user` 區塊**

將現有：

```jsx
        <div className="adm-topbar__user">
          <span className="adm-topbar__username">{admin.username}</span>
          <button className="adm-btn adm-btn--ghost" onClick={logout}>登出</button>
        </div>
```

替換為：

```jsx
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
```

- [ ] **Step 5: 將 OrderModal 從訂單分頁區塊移到 shell 層**

刪除訂單分頁內現有的這段（位於 `</div>` 結束 `adm-table-wrap` 之後、`</>` 之前）：

```jsx
          {modalOpen && selectedOrderNo && (
            <OrderModal
              orderNo={selectedOrderNo}
              token={token}
              onClose={closeModal}
              onStatusChange={() => {
                loadOrders(orders.page);
                setSummaryKey((k) => k + 1);
              }}
            />
          )}
```

改加到 products 分頁區塊之後、`adm-shell` 的結尾 `</div>` 之前：

```jsx
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
```

- [ ] **Step 6: 在 `frontend/assets/admin.css` 末端加入樣式**

```css
/* ── 通知中心 + 查看前台 ── */
.adm-topbar__store {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.adm-notif {
  position: relative;
  display: inline-flex;
}

.adm-notif__bell {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.adm-notif__bell:hover {
  background: rgba(0, 0, 0, 0.06);
}

.adm-notif__badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #d9534f;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
}

.adm-notif__backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
}

.adm-notif__panel {
  position: absolute;
  top: 48px;
  right: 0;
  z-index: 41;
  width: 320px;
  max-height: 70vh;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #e8d29e;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.adm-notif__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border-bottom: 1px solid #f0e6cc;
  font-weight: 700;
  color: #6b4e32;
}

.adm-notif__head-actions {
  display: inline-flex;
  gap: 8px;
}

.adm-notif__sound,
.adm-notif__readall {
  border: none;
  background: transparent;
  color: #6b7d52;
  font-size: 12px;
  cursor: pointer;
}

.adm-notif__readall:hover,
.adm-notif__sound:hover {
  text-decoration: underline;
}

.adm-notif__empty {
  padding: 24px 14px;
  text-align: center;
  color: #9b8a6f;
  font-size: 14px;
}

.adm-notif__list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.adm-notif__item {
  padding: 12px 14px;
  border-bottom: 1px solid #f6efdd;
  cursor: pointer;
}

.adm-notif__item:hover {
  background: #fbf3e0;
}

.adm-notif__item--unread {
  background: #eef4e2;
}

.adm-notif__item-top {
  font-weight: 700;
  color: #4a3a2a;
  font-size: 14px;
}

.adm-notif__item-sub {
  margin-top: 2px;
  color: #6b4e32;
  font-size: 12px;
}
```

- [ ] **Step 7: 確認可編譯**

Run: `cd frontend && npm run build`
Expected: 建置成功。

- [ ] **Step 8: 瀏覽器手動驗證**

啟動：`cd frontend && npm run dev`，瀏覽器開 `http://localhost:8080/admin` 並登入。

驗證清單：
1. Header 右側出現「查看前台」按鈕與鈴鐺；點「查看前台」→ 新分頁開啟前台 `/`。
2. 點鈴鐺 → 展開「未讀通知」面板，列出最近訂單（`新訂單 編號`、客戶・金額・相對時間）。
3. 建一筆新訂單（用前台 `/` 下單，或對後端 `POST /api/orders` 送測試單）→ 約 20 秒內鈴鐺出現未讀徽章 +1；若先點過鈴鐺（已解鎖音訊）且音效開，應聽到提示音。
4. 該筆在面板中以未讀底色highlight；點它 → 切到訂單分頁、開啟該筆訂單明細 modal，且徽章對應減少。
5. 「全部標示已讀」→ 徽章歸零；重新整理頁面後仍為已讀（localStorage 持久化）。
6. 切到「商品管理」分頁時，點通知仍能開啟訂單 modal（modal 已移到 shell 層）。

- [ ] **Step 9: Commit**

```bash
git add frontend/src/AdminApp.jsx frontend/assets/admin.css
git commit -m "feat(admin): header 新訂單通知鈴鐺+未讀清單與查看前台按鈕"
```

---

## Self-Review 註記

- **Spec 覆蓋**：輪詢/未讀（Task 1+2）、鈴鐺未讀中心+下拉+點擊看訂單（Task 3）、查看前台（Task 3 Step 4）、聲音+解鎖+開關（Task 2 + Task 3）、Wake Lock（Task 2）、相對時間（Task 1）、localStorage 持久化（Task 2）、後端零改動（全程未動 backend）。皆有對應任務。
- **通知範圍 = 新訂單**：面板只列訂單、徽章只算未讀訂單，未納入付款狀態通知，符合 spec。
- **型別一致**：hook 回傳的 `recentOrders/unread/unreadCount/soundOn/toggleSound/unlockAudio/markRead/markAllRead/refresh` 在 Task 3 全部按名使用；`formatRelativeTime`、`listAdminOrders` 簽名與既有程式一致。
- **OrderModal 移層**：Task 3 Step 5 明確刪除舊位置並加到 shell 層，避免重複渲染。
