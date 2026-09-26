## ADDED Requirements

### Requirement: 同規格品項合併計算庫存
系統 SHALL 在建立訂單時，將 `items` 中相同 `spec_id` 的數量加總後，再進行 2 粒裝雙數驗證、庫存驗證與扣庫存，且訂單 MUST 對每個 `spec_id` 只產生一筆 `OrderItem`。

#### Scenario: 重複規格總量超過庫存被拒
- **WHEN** 規格庫存為 3，且請求 `items=[{spec_id:S,qty:2},{spec_id:S,qty:2}]`
- **THEN** 回應 409 `INSUFFICIENT_STOCK`，且該規格庫存仍為 3

#### Scenario: 重複規格總量未超過庫存時合併成一列
- **WHEN** 規格庫存為 5，且請求 `items=[{spec_id:S,qty:2},{spec_id:S,qty:1}]` 且 `expected_total` 正確
- **THEN** 回應 201，訂單 `items` 只有一列 `qty=3`，規格庫存變為 2

#### Scenario: 2 粒裝以合併後數量判斷雙數
- **WHEN** 2 粒裝規格以 `items=[{spec_id:S,qty:1},{spec_id:S,qty:1}]` 下單
- **THEN** 合併數量為 2，雙數驗證通過（不回 `EVEN_QTY_REQUIRED`）
