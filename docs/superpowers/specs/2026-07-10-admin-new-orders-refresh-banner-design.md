# 訂單表格「有新訂單，點擊刷新」橫幅 — 設計

日期：2026-07-10
分支：feat/admin-tablet-new-order-alert

## 背景與問題

後台訂單管理頁的表格由 `loadOrders` 驅動，只在使用者動作（篩選、搜尋、翻頁、於明細改狀態）時重載，**沒有定時刷新**。通知中心（header 鈴鐺）則每 20s 輪詢並即時反映新單。

結果：admin 停在訂單管理**預設檢視（全部狀態、第 1 頁、無搜尋/日期）**時，新單進來只有鈴鐺會動，下方列表不會更新，必須自行手動刷新——體驗不佳。

正在**篩選或瀏覽其他訂單**的情況不在本次處理範圍：header 鈴鐺已能讓 admin 跳去查看新單。

## 目標

在預設檢視偵測到「表格尚未包含的新訂單」時，於表格上方顯示可點擊的橫幅提示；點擊即刷新表格（與上方統計卡）。

## 非目標

- 不改動通知輪詢、未讀中心、鈴鐺行為。
- 不在有篩選 / 非第 1 頁時顯示（交給鈴鐺）。
- 不做表格自動刷新（維持 admin 主動點擊，避免正在讀的列表突然跳動）。

## 觸發條件

```
isDefaultView = !filters.status && !filters.searchText.trim()
                && !filters.date_from && !filters.date_to
                && orders.page === 1
showBanner    = isDefaultView && newCount > 0
```

## 偵測邏輯（純函式，可單元測試）

於 `frontend/src/notifications.js` 新增：

```js
// recentOrders 中，created_at 比表格目前最新一列（sinceIso）更新的訂單。
// sinceIso 為 null（表格空、無基準）時，全部視為新。
export function newOrdersSince(recentOrders, sinceIso) {
  if (!recentOrders) return [];
  if (!sinceIso) return recentOrders.slice();
  return recentOrders.filter((o) => isAfter(o.created_at, sinceIso));
}
```

- 沿用既有、已測試的 `isAfter`（`isAfter(x, null) === false`，故需上面的 null 特例，避免表格空時漏報）。
- 資料來源：通知 hook 既有的 `notif.recentOrders`（每 20s 輪詢，page_size 10），**不新增任何輪詢或 API 呼叫**。
- 在 `AdminApp` 內：
  ```js
  const tableNewest = newestCreatedAt(orders.items);
  const newCount = newOrdersSince(notif.recentOrders, tableNewest).length;
  ```

在預設檢視下，通知輪詢與表格查詢皆為「無篩選、第 1 頁」的同一批最新訂單，故以 created_at 比較最新列可靠。

## UI

- 位置：`FilterStrip` 與訂單表格（`adm-table-wrap`）之間，橫跨全寬。
- 文案：`🔔 有 {newCount} 筆新訂單 · 點擊刷新`，整條可點。
- 樣式：`frontend/assets/admin.css` 新增 `.adm-new-orders-bar`，採現有 sage/強調色系，字級與觸控目標適合平板。
- 僅 `showBanner` 為真時渲染。

## 點擊行為

```js
onClick → loadOrders(1); setSummaryKey((k) => k + 1);
```

- 重載預設檢視 → 表格最新列 = 通知最新單 → `newCount` 歸 0 → 橫幅自動消失（「點了才消」）。
- 順帶 `setSummaryKey+1` 刷新上方統計卡（新單會影響總訂單數等）。
- 切換篩選 / 翻頁時 `isDefaultView` 轉為 false → 橫幅同樣不顯示。

## 消失方式

- 主要靠「點擊刷新後條件不再成立」自動消失。
- 離開預設檢視（篩選 / 非第 1 頁）也不顯示。
- 不做倒數自動隱藏（避免 admin 沒看到就消失而漏單）。

## 測試

- `frontend/src/notifications.test.js` 補 `newOrdersSince` 純邏輯測試：
  - 有比基準新的訂單 → 回傳該些；
  - 無更新訂單 → 回傳空；
  - 基準為 null（表格空）→ 全部視為新；
  - 相同 created_at → 不算新（`isAfter` 為嚴格大於）。
- 橫幅顯示條件與點擊刷新屬 UI 整合行為，沿用手動 / 瀏覽器驅動驗證。

## 影響檔案

- `frontend/src/notifications.js`（+1 純函式）
- `frontend/src/notifications.test.js`（+測試）
- `frontend/src/AdminApp.jsx`（計算 newCount + 橫幅 JSX + 點擊；`import { isAfter, newestCreatedAt, newOrdersSince }`）
- `frontend/assets/admin.css`（+`.adm-new-orders-bar` 樣式）
