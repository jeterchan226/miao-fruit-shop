## 1. 紅燈

- [ ] 1.1 新增 `tests/test_migrations.py`：建立 `miao_migration_test`、執行 `upgrade head`、`compare_metadata` 差異為空
- [ ] 1.2 新增往返測試：`downgrade base` → `upgrade head`
- [ ] 1.3 暫時在某 model 加一個欄位，確認一致性測試會失敗，再移除該欄位（證明測試有效）

## 2. 綠燈

- [ ] 2.1 視需要調整 `alembic/env.py`，允許以 `config.attributes` 或環境變數傳入 URL
- [ ] 2.2 若發現既有漂移，新增 migration 修正
- [ ] 2.3 執行 1.1、1.2 通過

## 3. 重構與驗證

- [ ] 3.1 將建立/刪除測試資料庫的邏輯整理成 fixture
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`
- [ ] 3.3 推到 PR 確認 CI 的 postgres service 下也能通過

## 4. 收尾

- [ ] 4.1 CLAUDE.md 的 Commands 區補充 migration 測試說明
- [ ] 4.2 以 `test(migrations): 驗證 Alembic migration 與 model 一致且可往返` 提交
