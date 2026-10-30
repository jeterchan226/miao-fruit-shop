## 1. 訂單狀態型別

- [ ] 1.1 在 `backend/tests/test_constants.py` 新增失敗測試：`get_args(OrderStatus)` 為四種訂單狀態
- [ ] 1.2 在 `backend/app/core/constants.py` 新增 `OrderStatus`，`OrderStatusUpdate.status` 改用它

## 2. 訂單狀態篩選

- [ ] 2.1 在 `backend/tests/test_admin_orders_api.py` 新增失敗測試：無效的訂單狀態回 422、空的訂單狀態回 422、OpenAPI 的 `status` 參數為 enum
- [ ] 2.2 補上四種訂單狀態各自篩選的測試，確認只回傳該狀態的訂單
- [ ] 2.3 route、`admin_order_service.list_orders`、`order_repo.list_filtered` 的 `status` 改為 `OrderStatus | None`

## 3. 驗證

- [ ] 3.1 `uv run ruff check .`
- [ ] 3.2 `uv run mypy app`
- [ ] 3.3 `uv run pytest -q`
