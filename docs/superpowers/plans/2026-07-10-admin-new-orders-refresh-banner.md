# 訂單表格「有新訂單，點擊刷新」橫幅 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 後台訂單管理預設檢視偵測到表格尚未包含的新訂單時，於表格上方顯示可點擊橫幅，點擊即刷新表格與統計卡。

**Architecture:** 新增一個純函式 `newOrdersSince`（可單元測試）判斷「比表格最新列更新的訂單」；`AdminApp` 讀既有的 `notif.recentOrders`（每 20s 輪詢，無新增 API）計算數量，僅在預設檢視渲染橫幅；點擊呼叫既有 `loadOrders(1)` 並 bump `summaryKey`。

**Tech Stack:** React（Vite）、Vitest、原生 CSS（admin.css，sage 設計系統）。

## Global Constraints

- 僅在預設檢視顯示：`!filters.status && !filters.searchText.trim() && !filters.date_from && !filters.date_to && orders.page === 1`。
- 不新增輪詢或 API 呼叫；資料來源為既有 `notif.recentOrders`。
- 不改動通知輪詢 / 未讀中心 / 鈴鐺行為。
- 文案固定為：`🔔 有 {newCount} 筆新訂單 · 點擊刷新`。
- 純邏輯放 `frontend/src/notifications.js` 並以 Vitest 測試；沿用既有 `isAfter`（`isAfter(x, null) === false`）。

---

### Task 1: `newOrdersSince` 純函式 + 單元測試

**Files:**
- Modify: `frontend/src/notifications.js`（在 `unreadOrders` 之後新增函式）
- Test: `frontend/src/notifications.test.js`（新增 import 與 describe 區塊）

**Interfaces:**
- Consumes: 既有 `isAfter(aIso, bIso)`（同檔）
- Produces: `newOrdersSince(recentOrders, sinceIso) => Array`（回傳 `recentOrders` 中 `created_at` 嚴格晚於 `sinceIso` 者；`sinceIso` 為 falsy 時回傳整份淺拷貝；`recentOrders` falsy 時回傳 `[]`）

- [ ] **Step 1: 寫失敗測試**

在 `frontend/src/notifications.test.js` 最上方 import 加入 `newOrdersSince`：

```js
import {
  formatRelativeTime,
  isAfter,
  newestCreatedAt,
  newOrdersSince,
  unreadOrders,
} from './notifications.js';
```

檔案結尾新增：

```js
describe('newOrdersSince', () => {
  it('回傳晚於基準者', () => {
    const since = ago(5000);
    const recent = [
      { order_no: 'A', created_at: ago(1000) },
      { order_no: 'B', created_at: ago(9000) },
    ];
    expect(newOrdersSince(recent, since).map((o) => o.order_no)).toEqual(['A']);
  });
  it('無更新訂單 → []', () => {
    const since = ago(0);
    expect(newOrdersSince([{ order_no: 'A', created_at: ago(1000) }], since)).toEqual([]);
  });
  it('基準為 null（表格空）→ 全部視為新', () => {
    const recent = [
      { order_no: 'A', created_at: ago(1000) },
      { order_no: 'B', created_at: ago(2000) },
    ];
    expect(newOrdersSince(recent, null).map((o) => o.order_no)).toEqual(['A', 'B']);
  });
  it('相同 created_at → 不算新', () => {
    const t = ago(3000);
    expect(newOrdersSince([{ order_no: 'A', created_at: t }], t)).toEqual([]);
  });
  it('recentOrders 為空 / undefined → []', () => {
    expect(newOrdersSince([], ago(0))).toEqual([]);
    expect(newOrdersSince(undefined, ago(0))).toEqual([]);
  });
});
```

- [ ] **Step 2: 執行測試確認失敗**

Run: `cd frontend && npx vitest run src/notifications.test.js`
Expected: FAIL，`newOrdersSince is not a function`（或 import 解析為 undefined）。

- [ ] **Step 3: 實作最小程式**

在 `frontend/src/notifications.js` 的 `unreadOrders` 函式之後新增：

```js
// recentOrders 中 created_at 嚴格晚於 sinceIso 者。
// sinceIso 為 falsy（表格空、無基準）時，全部視為新。
export function newOrdersSince(recentOrders, sinceIso) {
  if (!recentOrders) return [];
  if (!sinceIso) return recentOrders.slice();
  return recentOrders.filter((o) => isAfter(o.created_at, sinceIso));
}
```

- [ ] **Step 4: 執行測試確認通過**

Run: `cd frontend && npx vitest run src/notifications.test.js`
Expected: PASS（含新的 5 個 `newOrdersSince` 案例，原有測試不受影響）。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/notifications.js frontend/src/notifications.test.js
git commit -m "feat(admin): newOrdersSince 純函式偵測表格未含的新訂單"
```

---

### Task 2: AdminApp 橫幅整合 + 樣式

**Files:**
- Modify: `frontend/src/AdminApp.jsx`（import、計算值、橫幅 JSX）
- Modify: `frontend/assets/admin.css`（新增 `.adm-new-orders-bar`）

**Interfaces:**
- Consumes: Task 1 的 `newOrdersSince`；既有 `newestCreatedAt`、`notif.recentOrders`、`loadOrders`、`setSummaryKey`、`filters`、`orders`
- Produces: 無（UI 終點）

- [ ] **Step 1: 更新 import**

`frontend/src/AdminApp.jsx` 第 39 行：

```js
import { formatRelativeTime } from './notifications.js';
```

改為：

```js
import { formatRelativeTime, newestCreatedAt, newOrdersSince } from './notifications.js';
```

- [ ] **Step 2: 計算橫幅狀態**

在 `AdminApp` 的兩個 early return 之後、`return (` 之前（約第 1336–1338 行之間）插入：

```js
  const tableNewest = newestCreatedAt(orders.items);
  const newOrderCount = newOrdersSince(notif.recentOrders, tableNewest).length;
  const isDefaultView =
    !filters.status &&
    !filters.searchText.trim() &&
    !filters.date_from &&
    !filters.date_to &&
    orders.page === 1;
  const showNewOrdersBar = isDefaultView && newOrderCount > 0;
  const refreshOrders = () => {
    loadOrders(1);
    setSummaryKey((k) => k + 1);
  };
```

- [ ] **Step 3: 插入橫幅 JSX**

在 orders 分頁區塊，`<Alert message={listError} />` 之後、`<div className="adm-table-wrap">` 之前（約第 1407 行）插入：

```jsx
          {showNewOrdersBar && (
            <button className="adm-new-orders-bar" onClick={refreshOrders}>
              🔔 有 {newOrderCount} 筆新訂單 · 點擊刷新
            </button>
          )}
```

- [ ] **Step 4: 新增樣式**

在 `frontend/assets/admin.css` 末尾新增：

```css
/* 新訂單刷新提示條（僅預設檢視顯示） */
.adm-new-orders-bar {
  display: block;
  width: 100%;
  margin: 0 0 12px;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: var(--sage-900);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  cursor: pointer;
  transition: background 0.15s ease;
}
.adm-new-orders-bar:hover { background: var(--sage-700); }
```

- [ ] **Step 5: 建置確認無語法錯誤**

Run: `cd frontend && npm run build`
Expected: 建置成功、無錯誤。

- [ ] **Step 6: 手動 / 瀏覽器驗證**

1. `cd frontend && npm run dev`，瀏覽器開 `http://localhost:8080/admin`。
2. 以 mock（攔 `/api/admin/*`）或真實後端登入，停在預設檢視（全部狀態、第 1 頁、無搜尋/日期）。
3. 讓 `notif.recentOrders` 出現一筆比表格最新列更新的訂單（等 20s 輪詢或注入 mock）。
4. 預期：表格上方出現「🔔 有 1 筆新訂單 · 點擊刷新」橫幅。
5. 點橫幅 → 表格重載含新訂單、統計卡更新、橫幅消失。
6. 切一個狀態 chip 或翻頁 → 橫幅不顯示（`isDefaultView` 為 false）。

- [ ] **Step 7: Commit**

```bash
git add frontend/src/AdminApp.jsx frontend/assets/admin.css
git commit -m "feat(admin): 訂單表格新訂單刷新提示橫幅"
```

---

## Self-Review

- **Spec coverage:** 觸發條件（Task 2 Step 2 `isDefaultView`/`showNewOrdersBar`）、偵測純函式（Task 1）、UI 位置與文案（Task 2 Step 3）、點擊行為（Task 2 Step 2 `refreshOrders`）、樣式（Task 2 Step 4）、測試（Task 1）皆有對應任務。✅
- **Placeholder scan:** 無 TBD/TODO；所有程式碼與指令完整。✅
- **Type consistency:** `newOrdersSince` 簽章在 Task 1 定義、Task 2 使用一致；`newestCreatedAt`/`loadOrders`/`setSummaryKey`/`filters`/`orders` 皆為既有名稱。✅
