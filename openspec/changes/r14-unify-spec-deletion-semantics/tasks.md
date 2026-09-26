## 1. 紅燈

- [ ] 1.1 `tests/test_admin_products_api.py`：刪除後回 204，資料列仍在且 `deleted_at` 有值
- [ ] 1.2 `tests/test_products_api.py` 與後台列表：已刪除規格不出現；已下架（未刪除）規格仍出現在後台
- [ ] 1.3 `tests/test_orders_api.py`：以已刪除規格下單回 404
- [ ] 1.4 `tests/test_admin_order_service.py`：取消含已刪除規格的訂單會回補庫存
- [ ] 1.5 確認 1.1、1.2、1.4 失敗

## 2. 綠燈

- [ ] 2.1 `ProductSpec` 新增 `deleted_at`；新增 migration
- [ ] 2.2 `product_service.delete_spec` 改為設 `is_active=False`、`deleted_at=now()`；移除 `soft_delete_spec` 與 `spec_repo.delete`
- [ ] 2.3 `_to_public_product`、`_to_admin_product` 過濾 `deleted_at IS NULL`
- [ ] 2.4 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`
- [ ] 3.2 後台手動刪除一個測試規格，確認列表消失、既有訂單仍可檢視

## 4. 收尾

- [ ] 4.1 以 `fix(product): 規格刪除改為軟刪除並與下架區分` 提交
