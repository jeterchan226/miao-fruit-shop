# 規格照片改「包裝群組」共用 — 設計

日期：2026-07-26
分支：fix/shipping-fee-tiers（設計階段；實作建議另開分支）

## 背景與問題

甘露梨的商品照片不會因規格（5 台斤 / 10 台斤等）而不同，主要差異只在包裝大小（兩粒裝禮盒 vs. 一層裝箱）。但目前 `ProductImage` 用 `spec_id` 綁定「單一規格」，等於每個規格都要各自上傳一組專屬照片——即使兩個規格的實體包裝、外觀完全一樣，也要重複上傳兩次、各自維護排序。

## 目標

- 照片依「包裝群組」（兩粒裝 / 一層裝）管理，同群組底下所有規格共用同一組照片。
- 沿用現有 `ProductSpec.is_two_pack` 布林旗標作為分組依據，不新增獨立的群組欄位。
- 後台新增一個群組相片管理入口，一次維護一組照片，底下規格自動套用。

## 非目標

- 不支援兩組以外的包裝群組（`is_two_pack` 是布林，只有兩種值；未來若真的出現第三種包裝，需要另外設計 enum 欄位，不在本次範圍）。
- 不改動前台 `SpecCard.jsx` 的渲染邏輯（它吃的 `spec.images` 陣列格式不變，分組在後端解決）。
- 不處理 GCS 孤兒檔案清理（沿用現有刪除即呼叫 `gcs_service.delete_object` 的行為）。

## 資料模型

`ProductImage`：
- 移除 `spec_id`（FK → `product_specs.id`）與 `spec` relationship。
- 新增 `is_two_pack: bool | None`（nullable，預設 `None`）。
  - `True` → 兩粒裝群組
  - `False` → 一層裝群組
  - `None` → 商品層級 fallback 圖片（現況：前台未使用，維持原樣不動）

`ProductSpec`：移除 `images` relationship（不再直接持有圖片，改由 service 層依 `is_two_pack` 比對）。

`Product.images`（`lazy="selectin"`）不變，繼續一次撈出該商品所有圖片列，service 層據此分流成兩組。

## Migration

新增一個 alembic revision：

1. `product_images` 新增欄位 `is_two_pack BOOLEAN NULL`。
2. Backfill：
   ```sql
   UPDATE product_images
   SET is_two_pack = product_specs.is_two_pack
   FROM product_specs
   WHERE product_images.spec_id = product_specs.id;
   ```
   `spec_id IS NULL` 的列維持 `is_two_pack = NULL`。
3. Drop `spec_id` 欄位（含 FK、index）。
4. Downgrade：加回 `spec_id`（nullable），但**不**還原回原本對應到哪個規格——分組合併後已不可逆。Downgrade 僅用於緊急回滾 schema，需在 migration docstring 註明此限制。

**合併效應（預期行為，非 bug）**：目前 3 個規格中「5 台斤家庭箱」「10 台斤大箱」皆為 `is_two_pack=False`，若兩者先前已各自上傳不同照片，migration 後會合併成同一個「一層裝」相簿（依原 `sort_order, id` 排序）。「2 粒精緻禮盒」（`is_two_pack=True`）照片維持獨立成「兩粒裝」相簿。部署後管理員需要檢查一次合併後的一層裝相簿排序。

## 後端 API / Service

**`repositories/image_repo.py`**
- `list_by_product(product_id)`：查詢條件由 `spec_id IS NULL` 改為 `is_two_pack IS NULL`（語意不變）。
- 移除 `list_by_spec`。
- 新增 `list_by_group(session, product_id, is_two_pack: bool)`：`WHERE product_id = :pid AND is_two_pack = :flag`。

**`services/image_service.py`**
- 移除 `list_spec_images` / `register_spec_image` / `reorder_spec_images`。
- 新增對稱函式，皆吃 `(product_id, is_two_pack)`：
  - `list_group_images`
  - `register_group_image`（建立 `ProductImage(product_id=..., is_two_pack=..., url=..., sort_order=...)`）
  - `reorder_group_images`（比對條件改成 `img.product_id == product_id and img.is_two_pack == is_two_pack`）

**`api/routes/admin_images.py`**
- 移除 `/specs/{spec_id}/images`（GET/POST）與 `/specs/{spec_id}/images/reorder`（PATCH）三支。
- 新增：
  - `GET /api/admin/products/{product_id}/images/group/{group}`
  - `POST /api/admin/products/{product_id}/images/group/{group}`
  - `PATCH /api/admin/products/{product_id}/images/group/{group}/reorder`
  
  `group` 路徑參數為字面值 `"two_pack"` / `"single"`（用 `Literal["two_pack", "single"]` 型別），handler 內轉換成布林再呼叫 service。用文字字面值是為了網址可讀、避免布林字串轉換的邊界情況（例如 `"false"` 字串誤判為 truthy）。

**`services/product_service.py`**
- 新增純函式：
  ```python
  def _group_images(images: list[ProductImage], is_two_pack: bool) -> list[str]:
      return [img.url for img in images if img.is_two_pack == is_two_pack]
  ```
- `_to_public_spec` / `_to_admin_spec` 簽名改為吃 `(spec, product_images)`，內部呼叫 `_group_images(product_images, spec.is_two_pack)` 取代原本的 `spec.images`。
- `_to_public_product` / `_to_admin_product` 組裝規格列表時，把 `p.images` 一併傳入每個 spec 轉換呼叫。

## 前端（Admin）

**`api.js`**：`listSpecImages` / `registerSpecImage` / `reorderSpecImages` 改成 `listGroupImages` / `registerGroupImage` / `reorderGroupImages`，簽名皆為 `(token, productId, group)`，`group: 'two_pack' | 'single'`，對應到新後端路由。

**新增「商品照片管理」區塊**（位置：商品編輯頁內，規格列表之前）：
- 並排兩個相簿卡片：「兩粒裝相片」「一層裝相片」。
- 原本的 `SpecImageGallery`（key 為 `specId`）改名為 `GroupImageGallery`，key 改為 `(productId, group)`，上傳／刪除／拖曳排序邏輯不變，只換底層呼叫的 API 函式。

**規格編輯 / 新增 Modal（`SpecEditModal` 及對應建立流程）**：
- 移除原本內嵌的可編輯 `SpecImageGallery`。
- 改為唯讀預覽元件 `GroupImagePreview`（縮圖 grid，無上傳/刪除/拖曳），依目前 `form.is_two_pack` 顯示對應相簿，並附文字提示：「此規格使用『兩粒裝／一層裝』相片組，請至商品照片管理編輯」。
- 勾選 `is_two_pack` checkbox 時即時切換預覽對應相簿（不用等存檔），方便管理員確認選對群組。

**Storefront**：`SpecCard.jsx`、`api.js` 中 `spec.images` 的既有格式與消費方式不變，無需改動。

## 測試

後端：
- `test_image_repo.py`：`list_by_group` 依 `is_two_pack` 正確過濾；`list_by_product` 過濾 `is_two_pack IS NULL`。
- `test_image_service.py`：`register_group_image` / `reorder_group_images` 的建立與排序條件比對。
- `test_product_service.py`：`_group_images` 純函式測試（含 `is_two_pack=True/False` 各自过滤正確、空列表）；`_to_public_product`/`_to_admin_product` 驗證同群組規格共用同一組 `images`。
- `test_admin_images_api.py`：新的 `/products/{id}/images/group/{group}` 三支 CRUD/reorder 端點；確認舊 `/specs/{id}/images` 已移除（404）。
- migration：以現有 `tests/conftest.py` 的測試 DB 跑一次 `alembic upgrade head`，驗證 backfill 後資料正確（可在既有 migration 測試模式或手動驗證腳本中覆蓋）。

前端：
- 新增/沿用 `vitest` 對 `GroupImageGallery`／`GroupImagePreview` 的必要單元測試（若專案現有測試型態允許純邏輯測試；上傳/拖曳等互動維持既有的手動或瀏覽器驗證慣例，比照 `pricing.test.js` 只測純函式的作法）。
- 手動以瀏覽器驗證：後台上傳/刪除/排序兩個群組相片、切換規格 `is_two_pack` 後預覽同步變化、前台 SpecCard 輪播顯示正確群組照片。

## 影響檔案

後端：
- `backend/app/models/product_image.py`（欄位變更）
- `backend/app/models/product_spec.py`（移除 `images` relationship）
- `backend/app/repositories/image_repo.py`
- `backend/app/services/image_service.py`
- `backend/app/services/product_service.py`
- `backend/app/api/routes/admin_images.py`
- `backend/alembic/versions/`（新增一支 migration）
- `backend/tests/test_image_repo.py` / `test_image_service.py` / `test_product_service.py` / `test_admin_images_api.py` / `test_product_images_public.py`

前端：
- `frontend/src/api.js`
- `frontend/src/AdminApp.jsx`（`GroupImageGallery`、`GroupImagePreview`、商品照片管理區塊、Spec modal 調整）
