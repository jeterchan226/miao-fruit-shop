## ADDED Requirements

### Requirement: 商品照片只經由規格呈現
系統 SHALL 只在規格（`specs[].images`）中回傳照片，商品層級回應 MUST NOT 包含 `images` 或 `image` 欄位。

#### Scenario: 公開商品列表
- **WHEN** 呼叫 `GET /api/products`
- **THEN** 每個商品物件沒有 `images` 與 `image` 欄位，每個規格有 `images` 陣列

#### Scenario: 後台商品列表
- **WHEN** 已登入管理員呼叫 `GET /api/admin/products`
- **THEN** 每個商品物件沒有 `images` 與 `image` 欄位

### Requirement: 商品更新不接受 image 欄位
系統 SHALL 拒絕在商品更新請求中帶入 `image` 欄位。

#### Scenario: 送出 image 欄位
- **WHEN** 已登入管理員呼叫 `PATCH /api/admin/products/{id}` 並帶 `{"image": "x.jpg"}`
- **THEN** 回應 422
