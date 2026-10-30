## 1. 鎖住公開下單回應欄位

- [ ] 1.1 寫測試 `test_create_order_response_excludes_admin_fields`（`backend/tests/test_orders_api.py`）：用帶齊顧客個資與 LINE 身份的請求下單，斷言回應頂層 key 集合與 `items[0]` 的 key 集合等於規格列出的欄位
- [ ] 1.2 暫時在 `OrderRead` 加 `customer_name: str = "x"`，確認測試失敗；對 `OrderItemRead` 同樣確認一次，然後還原
- [ ] 1.3 確認測試在未改動的回應結構下通過，`git diff` 只剩測試檔

## 2. 驗證

- [ ] 2.1 `uv run ruff check .`
- [ ] 2.2 `uv run mypy app`
- [ ] 2.3 `uv run pytest -q`
