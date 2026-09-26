## Context

`create_order` 與 `_replace_items` 都是「逐項 `get_for_update` → 逐項比對 `stock_qty < qty`」。同一個 `spec_id` 兩次 `get_for_update` 會拿到 identity map 中的同一物件，但比對用的是單行 qty，因此總量不受限制。

## Goals / Non-Goals

**Goals:**
- 以合併後數量做所有驗證與扣減。
- 前台、後台兩條路徑行為一致。

**Non-Goals:**
- 不在此處處理鎖順序（r05）或抽共用函式（r22）。
- 不改 API schema 形狀。

## Decisions

- **在 service 層合併，而非在 schema 層拒絕重複 `spec_id`**：前端購物車理論上不會送出重複規格，但合併對使用者更友善，且後台編輯 UI 也可能產生重複列。替代方案「Pydantic validator 拒絕重複」較簡單但會把合法意圖變成 422。
- 合併採 `dict[int, int]`，保留首次出現順序（Python dict 保序），讓 `OrderItem` 順序與使用者輸入一致。

## Risks / Trade-offs

- [回應 `items` 列數可能少於請求列數] → 前端只用回應顯示結果，不依賴列數對應；在 proposal 標示行為變更。
- [與 r05、r22 修改同一段程式碼] → 建議實作順序 r01 → r05 → r22；r22 會把本 change 的合併邏輯搬進共用函式。
