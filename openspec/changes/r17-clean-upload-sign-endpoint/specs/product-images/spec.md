## ADDED Requirements

### Requirement: 上傳簽名不存取資料庫
系統 SHALL 在產生上傳簽名 URL 時不開啟資料庫連線。

#### Scenario: 資料庫無法連線時簽名
- **WHEN** 資料庫 session 依賴會拋出例外，管理員呼叫 `POST /api/admin/uploads/sign`
- **THEN** 回應 200 並回傳 `signed_url` 與 `public_url`

### Requirement: 上傳物件使用固定前綴
系統 SHALL 將新上傳的物件命名為 `products/uploads/<隨機 hex>.<副檔名>`，MUST NOT 使用寫死的商品 id 作為路徑。

#### Scenario: 產生物件名稱
- **WHEN** 請求簽名上傳 `photo.jpg`
- **THEN** `public_url` 路徑以 `products/uploads/` 開頭
