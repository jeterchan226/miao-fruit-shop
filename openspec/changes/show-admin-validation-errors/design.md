## Context

#95 來自 PR #90 的 review，當時僅靜態閱讀。本 change 已確認可觸發：

- 登入帳密留白：`POST /api/admin/auth/login` 以空字串送出時回傳 422，`detail` 為兩個 `missing` 物件（實際呼叫確認）。登入輸入框沒有 `required`。
- 規格售價或庫存填小數：`type="number"` 未限制整數，且表單不經 `<form>` 驗證，`Number("1.5")` 送出後被 `int` 欄位拒絕（`int_from_float`，以 Pydantic schema 確認）。

`AdminApp.jsx` 的七處 catch 以 `err?.data?.detail || fallback` 取訊息後渲染，`orderEditErrorMessage` 也回傳 `data.detail`。專案沒有 error boundary，React 對物件 child 拋錯時整個後台卸載。`ApiError` 建立於 `request` 與 `loginAdmin` 兩處，所有讀取 `detail` 的路徑都經過它。

## Goals / Non-Goals

**Goals:**

- 任何 API 回應的非字串 `detail` 都不會讓後台崩潰，並顯示易讀訊息。
- 字串 `detail` 與各操作的 fallback 訊息行為不變。

**Non-Goals:**

- 不新增後端 `RequestValidationError` handler，不改 422 回應格式。
- 不調整表單輸入檢查（登入必填、售價與庫存限整數）；本 change 只處理錯誤呈現。
- 不把驗證錯誤對應到個別欄位。
- 不新增 error boundary。
- 商店頁結帳：`Cart.jsx` 依 `status === 422` 顯示自己的訊息，不讀陣列 `detail`，維持原樣。

## Decisions

### 在 `ApiError` 建構時正規化，而非修改各 catch 處

`ApiError` 是唯一匯流點，正規化放在這裡即涵蓋現有與未來的 catch，`err.message` 也同時得到字串。逐處包函式要改八處以上，且新程式碼容易漏掉。

規則：`data.detail` 存在且不是字串時，以複本把 `detail` 換成固定訊息；`null`、未定義維持原狀，讓 `||` 走 fallback。空陣列也算非字串。不修改傳入的 `data` 物件。

### 改用前端正規化，不加後端 handler

後端 handler 會讓 422 回傳字串 `detail`，但要改動所有 API 共通的回應格式，且前端仍需防禦其他非字串內容。前端修改範圍較小，也符合 ticket「統一把 `detail` 轉成字串」的方向。

### 使用固定的繁體中文訊息，不串接 Pydantic 訊息

Pydantic 的 `msg` 是英文，`loc` 是內部欄位名，對管理員沒有幫助。文案沿用 `Cart.jsx` 422 訊息的語氣，不提「收件資訊」，因為後台表單未必有該欄位。訊息定義於 `ApiError` 所在模組。

### 把 `ApiError` 移到不觸碰 `window` 的模組

`api.js` 載入時會寫入 `window.MiaoApi`，而 vitest 跑在 node 環境（未安裝 jsdom），測試無法 import。把 `ApiError` 移到新模組 `frontend/src/apiError.js`，`api.js` 匯入後維持原本的 `export` 與 `window.MiaoApi` 內容，現有 import 不必改。

## Testing Decisions

- **入口**：純函式／類別層級的 vitest，直接建構 `ApiError`，不經過 HTTP 或畫面。選這個入口因為它是最高的既有可測 seam：前端沒有元件測試環境，為此引入 jsdom 不符合比例。
- **既有範例**：`frontend/src/orderEdit.test.js` 的 `orderEditErrorMessage` 測試。
- **涵蓋**：物件陣列、物件、空陣列的 `detail` 轉為固定訊息；字串原樣保留；無 `detail` 與 `null` 維持 falsy；`err.message` 為字串；傳入的 `data` 未被修改；`code`、其他欄位（如 `total`）保留。
- **Scenario 對應**：前兩個 Scenario 的畫面部分由測試保證 `detail` 為字串，再由實作時在本機以空白登入與小數售價手動確認。

## Risks / Trade-offs

- [訊息不指出是哪個欄位] → 管理員需自行檢查；後續可另開 ticket 補表單檢查。
- [手動確認才涵蓋畫面] → 邏輯集中在單一類別，自動測試保護正規化本身。
- [PR #90 尚未合入 dev，也改動 `orderEdit.js`] → 本 change 不改 `orderEdit.js`，不會衝突。
