## 1. 紅燈

- [ ] 1.1 `tests/test_admin_order_service.py` 新增三個情境（台灣凌晨納入、前一天深夜排除、date_to 最後一刻納入），測試連線 `SET TIME ZONE 'UTC'`
- [ ] 1.2 新增 `to_business_day_range` 單元測試（含只給其中一端的情況）
- [ ] 1.3 執行並確認「台灣凌晨」情境失敗

## 2. 綠燈

- [ ] 2.1 `core/config.py` 新增 `business_timezone: str = "Asia/Taipei"`；`pyproject.toml` 加入 `tzdata`
- [ ] 2.2 service 層實作 `to_business_day_range`，`order_repo.list_filtered` 改收 `created_from` / `created_before`（aware datetime）
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 更新 `tests/test_order_repo.py` 既有日期篩選測試為新參數
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `fix(admin-order): 日期篩選改以 Asia/Taipei 營業日解讀` 提交
