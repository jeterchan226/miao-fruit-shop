## 1. 紅燈

- [ ] 1.1 移除 `.github/workflows/ci.yml` mypy 步驟的 `continue-on-error: true`，並將步驟名稱改為 `Mypy`
- [ ] 1.2 本地執行 `uv run mypy app`，確認目前為 10 個錯誤（記錄於 PR 說明）

## 2. 綠燈

- [ ] 2.1 `line_service.py` 新增 `FlexJson = dict[str, Any]` 並替換所有裸 `dict`
- [ ] 2.2 `pyproject.toml` 新增 `google.cloud.*`、`google.oauth2.*` 的 `ignore_missing_imports` override
- [ ] 2.3 `gcs_service.py:29` 加上 `# type: ignore[no-untyped-call]`
- [ ] 2.4 執行 `uv run mypy app` 確認 `Success: no issues found`

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`
- [ ] 3.2 推到 PR 確認 CI mypy 步驟為必要且通過

## 4. 收尾

- [ ] 4.1 更新 CLAUDE.md 中「non-blocking mypy」的描述
- [ ] 4.2 以 `ci(backend): mypy strict 改為必要檢查並修正現有型別錯誤` 提交
