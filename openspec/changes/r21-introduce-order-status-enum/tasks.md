## 1. 紅燈

- [ ] 1.1 新增 `tests/test_order_status.py`：轉移表鍵集合等於 `set(OrderStatus)`；`NOT_EDITABLE_STATUSES` 為 `OrderStatus` 子集
- [ ] 1.2 `tests/test_admin_orders_api.py`：`{"status":"canceled"}` 回 422（確認既有行為維持）
- [ ] 1.3 確認 1.1 因列舉不存在而失敗

## 2. 綠燈

- [ ] 2.1 新增 `OrderStatus(StrEnum)`
- [ ] 2.2 替換 `order_service.initial_status`、`admin_order_service` 轉移表與不可編輯集合、`order_repo.summary`、`OrderStatusUpdate`
- [ ] 2.3 `Order.status` 標註為 `Mapped[OrderStatus]`（`String` 欄位）
- [ ] 2.4 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 `grep -rn '"pending_payment"\|"ready"\|"shipping"\|"cancelled"' backend/app` 除列舉定義外無結果
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `refactor(order): 訂單狀態改用 OrderStatus 列舉` 提交
