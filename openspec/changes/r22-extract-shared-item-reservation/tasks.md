## 1. 特性測試（鎖住現有行為）

- [ ] 1.1 `tests/test_admin_order_service.py` 補齊：後台以下架規格編輯回 404、2 粒裝奇數回 409、價格快照
- [ ] 1.2 補齊取消回補庫存（含已不存在規格略過）
- [ ] 1.3 執行確認全數通過（作為重構安全網；若有失敗代表發現既有 bug，先記錄並修正）

## 2. 紅燈：新介面

- [ ] 2.1 `tests/test_order_service.py` 新增 `lock_and_validate`、`commit_reservation`、`release_items` 的單元測試
- [ ] 2.2 確認因函式不存在而失敗

## 3. 綠燈

- [ ] 3.1 實作三個函式與 `_to_item_read`
- [ ] 3.2 `create_order`、`_replace_items`、`change_order_status` 改用新函式
- [ ] 3.3 執行全部測試通過

## 4. 重構與驗證

- [ ] 4.1 移除兩個 service 中已無用的重複程式
- [ ] 4.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 5. 收尾

- [ ] 5.1 以 `refactor(order): 抽出下單與後台編輯共用的品項保留邏輯` 提交
