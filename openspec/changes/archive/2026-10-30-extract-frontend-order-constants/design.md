## Context

後端 `backend/app/core/constants.py` 已定義 `ORDER_SOURCE_STOREFRONT`、`ORDER_SOURCE_ADMIN`、`PAYMENT_METHOD_TRANSFER`。前端仍有五個字串常值，分布在四處：`AdminApp.jsx` 的 `SOURCE_OPTIONS`（兩個值）、`SourceBadge`，`notifications.js` 的 `isCustomerOrder`，`Cart.jsx` 的 `buildOrderPayload`。前端目前沒有常數模組，也沒有元件測試工具（只有 vitest，未裝 jsdom 或 testing-library），`Cart.jsx` 與 `AdminApp.jsx` 因此沒有自動測試。

## Goals / Non-Goals

**Goals:**

- 這五個字串常值改引用前端單一常數模組。
- 測試鎖定常數的值，讓打錯字或誤改會被 `npm run test` 擋下。

**Non-Goals:**

- 不做前後端共用定義或產生常數（如由 OpenAPI 產生）；兩邊仍各有一份。
- 不改畫面文案、API 請求內容與提醒行為。
- 不收斂其他字串常值，例如訂單狀態、送達時段。
- 不導入 jsdom、testing-library 或元件測試；不為了測試而把 `buildOrderPayload` 抽出元件。
- 不改寫既有測試裡的字串常值。

## Decisions

**1. 新增 `frontend/src/constants.js`，匯出與後端同名的常數。**
`ORDER_SOURCE_STOREFRONT`、`ORDER_SOURCE_ADMIN`、`PAYMENT_METHOD_TRANSFER` 三個具名匯出，命名對齊後端，方便對照與搜尋。
替代方案：包成 `ORDER_SOURCE = { ADMIN, STOREFRONT }` 物件：拼錯屬性只得到 `undefined`，建置不會報錯；具名匯出拼錯時 Vite 建置就會失敗。

**2. 只放目前用到的常數，不加型別或工具函式。**
不抽 `isAdminOrder` 之類的 helper，判斷式維持原位只換掉字串，diff 最小。

**3. 檔頭註明值須與後端一致。**
無法跨語言 import，以註解指向後端檔案。

**4. `notifications.js` 與 `AdminApp.jsx` 只改引用，文案與結構不變。**
`SOURCE_OPTIONS` 的「全部」空字串是「不篩選」，不是訂單來源，維持原樣。

## Testing Decisions

Seams 於 spec 階段決定，如下。

- **主要入口：純函式／模組**（前端現有最高 seam）。新增 `frontend/src/constants.test.js`，斷言三個常數的值，鎖定與後端 API 的契約。
- **不改的安全網：** `frontend/src/notifications.test.js` 的「排除代客下單」與 `isCustomerOrder` 測試用字串常值，代表 API 回傳的值，全程不修改、須維持通過。這是 `isCustomerOrder` 改用常數後行為不變的證明。
- **Prior art：** `notifications.test.js`、`pricing.test.js` 的純邏輯 vitest 寫法。
- **紅燈方式：** 先寫 `constants.test.js`，模組不存在所以失敗；其餘為行為不變的替換，由既有測試保護。
- **無自動測試的三處（`SOURCE_OPTIONS`、`SourceBadge`、`buildOrderPayload`）：** 由 `npm run build` 擋住匯入錯誤（具名匯入不存在時建置失敗），再以搜尋確認非測試檔不留字串常值，值本身由 `constants.test.js` 鎖定。
- 後端不動，不跑 ruff、mypy、pytest。

## Risks / Trade-offs

- [前後端定義漂移] → 非本次範圍；`constants.test.js` 把前端的值寫死，後端改值時須同步，檔頭註解提醒。
- [`payment_method` 變成 `undefined` 時 JSON 會省略欄位，後端預設 `transfer`，錯誤不會浮現] → 具名匯入由建置擋下，且本次只有一處引用。
- [`Cart.jsx`、`AdminApp.jsx` 無自動測試] → 改動僅替換字串為常數，由建置、搜尋與 `constants.test.js` 涵蓋，不為此引入新工具。

## Open Questions

（無）
