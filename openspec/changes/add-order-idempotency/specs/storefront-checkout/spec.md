## ADDED Requirements

### Requirement: 下單冪等性

系統 SHALL 以 `POST /api/orders` 的 `Idempotency-Key` header 辨識同一次送單：同一個 key 最多成立一張訂單，重送時 SHALL 回傳 201 與原訂單內容，不扣庫存、不核對金額、不比對請求內容。未帶此 header 的請求 SHALL 視為一筆新訂單。代客下單不適用此機制。

#### Scenario: 相同 key 重送

- **WHEN** 系統收到兩個帶相同 `Idempotency-Key` 的下單請求
- **THEN** 只成立一張訂單，兩次皆回傳 201 且 `order_no` 相同

#### Scenario: 重送不重複扣庫存

- **WHEN** 相同 key 的訂單已成立後再次收到請求
- **THEN** 規格庫存只扣一次

#### Scenario: 原訂單成立後條件改變

- **WHEN** 相同 key 的訂單已成立，之後規格調價或售完，再次收到請求
- **THEN** 系統回傳原訂單，不回傳 `PRICE_CHANGED` 或 `INSUFFICIENT_STOCK`

#### Scenario: 相同 key 同時送達

- **WHEN** 兩個帶相同 key 的請求同時送達
- **THEN** 只成立一張訂單，庫存只扣一次，兩個請求皆回傳 201 且 `order_no` 相同

#### Scenario: 相同 key 同時搶最後庫存

- **WHEN** 兩個帶相同 key 的請求同時送達，且規格庫存只夠成立一張訂單
- **THEN** 只成立一張訂單，兩個請求皆回傳 201 且 `order_no` 相同

#### Scenario: 失敗的請求不佔用 key

- **WHEN** 帶某 key 的請求因 `PRICE_CHANGED` 被拒，之後以相同 key 送出合法請求
- **THEN** 訂單成立

#### Scenario: 不同 key

- **WHEN** 系統收到兩個內容相同但 key 不同的請求
- **THEN** 成立兩張訂單並各自扣庫存

#### Scenario: 未帶 key

- **WHEN** 系統收到兩個未帶 `Idempotency-Key` 且內容相同的請求
- **THEN** 成立兩張訂單並各自扣庫存

#### Scenario: 公開回應不含 key

- **WHEN** 顧客帶 key 下單成功
- **THEN** 回應不含 `idempotency_key`

### Requirement: Idempotency-Key 格式驗證

系統 MUST 以 422 拒絕長度不在 1 到 128 字元之間的 `Idempotency-Key`。

#### Scenario: 空的 key

- **WHEN** 請求的 `Idempotency-Key` 為空字串
- **THEN** 系統回傳 422，不成立訂單

#### Scenario: 過長的 key

- **WHEN** 請求的 `Idempotency-Key` 超過 128 字元
- **THEN** 系統回傳 422，不成立訂單

### Requirement: 商店頁防重複送出

商店頁 SHALL 在送出訂單後立即鎖住送出動作直到請求結束，並在送出中停用送出按鈕。每個請求 SHALL 帶 `Idempotency-Key`：訂單內容未變的重試沿用同一個 key，訂單內容改變或訂單成立後 SHALL 改用新的 key。

#### Scenario: 送出中再次點擊

- **WHEN** 訂單送出中
- **THEN** 送出按鈕不可點選並顯示送出中

#### Scenario: 連續快速點擊

- **WHEN** 顧客在畫面更新前連按兩次送出訂單
- **THEN** 商店頁只發出一個下單請求

#### Scenario: 失敗後重試沿用 key

- **WHEN** 送出因網路錯誤或逾時失敗，顧客未改內容再次送出
- **THEN** 請求帶與前次相同的 `Idempotency-Key`

#### Scenario: 改內容後換 key

- **WHEN** 送出失敗後顧客修改訂單內容再次送出
- **THEN** 請求帶新的 `Idempotency-Key`

#### Scenario: 訂單成立後再次結帳

- **WHEN** 訂單成立後顧客以相同內容再次結帳
- **THEN** 請求帶新的 `Idempotency-Key`，成立另一張訂單

## REMOVED Requirements

### Requirement: 下單沒有冪等性保護

**Reason**: 重複送出會成立多張訂單並重複扣庫存與通知。

**Migration**: 由「下單冪等性」與「商店頁防重複送出」取代；未帶 `Idempotency-Key` 的請求維持原行為。
