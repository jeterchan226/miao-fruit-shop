## 1. 紅燈

- [ ] 1.1 `tests/test_admin_orders_api.py`：`status=canceled` 回 422
- [ ] 1.2 `status=cancelled` 只回已取消訂單；不帶參數回全部
- [ ] 1.3 確認 1.1 失敗

## 2. 綠燈

- [ ] 2.1 `admin_orders.list_orders` 的 `status` 型別改為 `OrderStatus | None`（或暫時 `Literal`）
- [ ] 2.2 service 與 repo 的參數型別同步
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 grep `frontend/src` 的 `listOrders` / `status=` 呼叫，確認沒有非列舉值
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `fix(admin-order): 訂單列表狀態篩選改為列舉驗證` 提交
