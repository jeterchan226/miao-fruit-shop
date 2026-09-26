## Why

審查 #12：`Product.image` 是 GCS 上線前的單圖欄位（model 註解寫「GCS 上線後逐步淘汰」），至今仍被 `_get_images` 當作 fallback、`ProductUpdate` 可寫入、`seed-product` 寫入 `assets/product_5.jpg`。此外 API 回應中的商品層級 `images` 欄位會把所有群組的照片混在一起，前台只使用 `spec.images`，後台也未使用它。兩者都是容易誤用的遺留介面。

## What Changes

- **BREAKING**：`PublicProductRead` 與 `AdminProductRead` 移除商品層級 `images` 欄位。
- **BREAKING**：`ProductUpdate` 移除 `image` 欄位（送出時回 422，因為 `extra="forbid"`）。
- 新增 Alembic migration 刪除 `products.image` 欄位（downgrade 還原為 nullable 欄位）。
- `seed-product` 不再寫入 `image`。

## Capabilities

### New Capabilities
- `product-catalog`: 商品與規格的公開／後台資料形狀。

### Modified Capabilities
（無）

## Impact

- `backend/app/models/product.py`、`backend/app/schemas/product.py`、`backend/app/services/product_service.py`、`backend/app/cli.py`
- 新 migration：`drop_products_image`
- 前端確認無使用 `product.images`（目前 `App.jsx` 只讀 `spec.images`；`AdminApp.jsx:1531` 讀的是 `s.images`，即規格）
