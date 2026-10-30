Ticket: #95

## Why

後台表單能實際觸發 FastAPI 預設的 422：登入帳密留白、規格售價或庫存填小數，回應的 `detail` 都是物件陣列。後台把 `detail` 直接交給 React 渲染，React 不接受物件作為 child，而後台沒有 error boundary，管理員會看到整頁空白。

## What Changes

- 前端 API 用戶端在建立錯誤時統一處理 `detail`：不是字串就換成一則固定的繁體中文訊息。
- 字串 `detail`（業務錯誤）照原文顯示；回應沒有 `detail` 時，各操作原有的 fallback 訊息不變。
- 不改後端 422 回應格式，也不改任何表單的輸入檢查。

## User Stories

1. 身為管理員，我想要在送出格式不合的資料時看到看得懂的錯誤訊息，以便修正輸入後重送，而不是面對空白頁。
2. 身為管理員，我想要業務錯誤維持原本的具體訊息，以便知道操作失敗的確切原因。

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `api-platform`: 新增後台呈現非字串錯誤內容的要求。

## Impact

- 前端 API 用戶端的錯誤類別，以及所有經由它讀取 `detail` 的後台畫面。
- 無 API、資料庫或依賴變更。商店頁結帳已依狀態碼顯示自己的訊息，行為不變。
