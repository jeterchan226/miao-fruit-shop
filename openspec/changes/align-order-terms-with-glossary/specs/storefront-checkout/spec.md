## MODIFIED Requirements

### Requirement: 下單失敗提示

商店頁 SHALL 依錯誤類型提示顧客，並停留在轉帳資訊步驟；不自動清空購物車。

#### Scenario: 價格已更新

- **WHEN** 下單回傳 `PRICE_CHANGED`
- **THEN** 顯示新的訂單合計並請顧客重新確認後再送出

#### Scenario: 規格不存在

- **WHEN** 下單回傳 `NOT_FOUND`
- **THEN** 請顧客重新整理頁面後再加入購物車

#### Scenario: 庫存不足

- **WHEN** 下單回傳 `INSUFFICIENT_STOCK`
- **THEN** 顯示庫存不足訊息

#### Scenario: 雙數限制

- **WHEN** 下單回傳 `EVEN_QTY_REQUIRED` 且未帶錯誤訊息
- **THEN** 顯示以「兩粒裝」稱呼包裝類型的雙數購買提示
