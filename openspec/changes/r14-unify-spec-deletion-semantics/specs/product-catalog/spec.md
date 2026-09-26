## ADDED Requirements

### Requirement: 規格刪除為軟刪除
系統 SHALL 在管理員刪除規格時保留該規格資料列並標記 `deleted_at`，已刪除的規格 MUST NOT 出現在公開或後台的商品規格列表，也 MUST NOT 可被下單。

#### Scenario: 刪除規格
- **WHEN** 已登入管理員呼叫 `DELETE /api/admin/specs/{id}`
- **THEN** 回應 204，資料庫中該規格仍存在且 `deleted_at` 不為 null

#### Scenario: 已刪除規格不出現在列表
- **WHEN** 呼叫 `GET /api/products` 或 `GET /api/admin/products`
- **THEN** 回應中不包含已刪除的規格

#### Scenario: 無法以已刪除規格下單
- **WHEN** 以已刪除規格的 `spec_id` 下單
- **THEN** 回應 404 `NOT_FOUND`

#### Scenario: 取消含已刪除規格的歷史訂單
- **WHEN** 取消一張含已刪除規格（qty 2）的 `pending_payment` 訂單
- **THEN** 該規格的 `stock_qty` 增加 2

### Requirement: 下架與刪除區分
系統 SHALL 以 `is_active=false` 表示暫時下架（後台仍可見並可重新上架），以 `deleted_at` 表示刪除（後台不可見）。

#### Scenario: 下架規格仍在後台
- **WHEN** 規格 `is_active=false` 且 `deleted_at` 為 null
- **THEN** 後台商品列表仍顯示該規格，公開列表不顯示
