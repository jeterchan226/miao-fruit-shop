## 1. 紅燈

- [ ] 1.1 `tests/test_products_api.py`：公開商品回應不含 `images`、`image`
- [ ] 1.2 `tests/test_admin_products_api.py`：後台商品回應不含 `images`、`image`；`PATCH` 帶 `image` 回 422
- [ ] 1.3 確認測試失敗

## 2. 綠燈（第一階段：程式不再使用欄位）

- [ ] 2.1 `schemas/product.py` 移除 `PublicProductRead.images`、`AdminProductRead.images`、`ProductUpdate.image`
- [ ] 2.2 `product_service` 移除 `_get_images` 與相關指派
- [ ] 2.3 `models/product.py` 移除 `image` mapped column；`cli.seed_product` 移除 `image=`
- [ ] 2.4 執行 1.x 測試通過；更新 `test_product_service.py` 中相關斷言

## 3. 第二階段：migration

- [ ] 3.1 新增 migration `drop_products_image`（upgrade 刪欄位；downgrade 加回 nullable 欄位並註明資料無法還原）
- [ ] 3.2 若 r09 已完成，確認 migration 一致性測試通過；否則手動 `alembic upgrade head` / `downgrade -1` 驗證
- [ ] 3.3 第二階段需在第一階段部署後、另一次部署才合併（在 PR 說明標註）

## 4. 重構與驗證

- [ ] 4.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`
- [ ] 4.2 frontend `npm run build` 通過，前台商品頁與後台商品頁手動確認照片正常

## 5. 收尾

- [ ] 5.1 以 `refactor(product): 移除遺留的 Product.image 與商品層級 images 欄位` 提交（兩階段各一個 commit）
