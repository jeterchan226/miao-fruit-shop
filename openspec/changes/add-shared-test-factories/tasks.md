## 1. 工廠：訂單

- [ ] 1.1 記下目前 `uv run pytest -q` 的通過數，作為基準
- [ ] 1.2 寫失敗測試 `tests/test_factories.py`：預設訂單可寫入、覆寫生效、不存在的欄位丟 `TypeError`
- [ ] 1.3 新增 `tests/factories.py` 的 `build_order`，讓測試通過

## 2. 工廠：規格與含訂單品項的訂單

- [ ] 2.1 寫失敗測試：`create_spec` / `create_specs` 回傳有 id 的規格、多規格同商品且順序不變
- [ ] 2.2 實作 `build_spec`、`build_product`、`create_spec`、`create_specs`
- [ ] 2.3 寫失敗測試：`create_order_with_items` 金額由 lines 算出、指定金額時覆寫優先
- [ ] 2.4 實作 `build_order_item`、`create_order_with_items`
- [ ] 2.5 寫失敗測試：工廠寫入後未 commit，另一條連線讀不到；讓測試通過

## 3. 改用工廠：ticket 列出的檔案

- [ ] 3.1 `test_admin_order_service.py`：`_make_order` 改薄包裝，`_make_order_with_item`、`_make_product_and_spec` 與手寫的 `Product` / `ProductSpec` / `OrderItem` 改用工廠；跑該檔
- [ ] 3.2 `test_admin_orders_api.py`：`_make_order` 改薄包裝，`_make_order_with_spec` 改用工廠；跑該檔
- [ ] 3.3 `test_order_repo.py`：`_make_order` 改薄包裝（保留 2030 等值），三處 `Order(...)` 字面值改用工廠；跑該檔
- [ ] 3.4 `test_admin_order_concurrency.py`：`seeded` 改用 `build_*`，`commit` 與 `_delete_seeded` 不動；跑該檔

## 4. 改用工廠：其餘重複

- [ ] 4.1 `test_line_service.py`、`test_order_items.py` 的訂單字面值與 `_spec` / `_seed_specs` 改用工廠；跑該檔
- [ ] 4.2 `test_order_service.py`、`test_orders_api.py`、`test_admin_create_order_api.py` 的規格 seed 改用工廠；跑該檔

## 5. 驗證

- [ ] 5.1 `uv run ruff check .`
- [ ] 5.2 `uv run mypy app`
- [ ] 5.3 `uv run pytest -q`：通過數等於基準加上 `test_factories.py` 新增數
- [ ] 5.4 `backend/tests/` 中帶欄位的 `Order(` 只出現在 `factories.py`
- [ ] 5.5 `git diff` 確認 `assert` 行未變動、`backend/app/` 無變更
