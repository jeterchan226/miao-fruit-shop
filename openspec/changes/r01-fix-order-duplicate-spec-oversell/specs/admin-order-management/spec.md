## ADDED Requirements

### Requirement: 後台替換品項時合併同規格數量
系統 SHALL 在後台編輯訂單品項時，將相同 `spec_id` 的數量加總後才驗證庫存與扣庫存，且替換後的訂單 MUST 對每個 `spec_id` 只有一筆 `OrderItem`。

#### Scenario: 後台以重複規格超量編輯被拒
- **WHEN** 訂單原品項已加回庫存後可用量為 3，後台送出 `items=[{spec_id:S,qty:2},{spec_id:S,qty:2}]`
- **THEN** 回應 409 `INSUFFICIENT_STOCK`，訂單品項與庫存皆維持編輯前狀態
