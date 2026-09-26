## Why

審查 #10：`pyproject.toml` 設定 mypy strict，但目前有 10 個錯誤（`line_service.py` 8 個 `dict` 缺型別參數、`gcs_service.py` 缺 google-cloud stub 與未型別化呼叫），而 CI 的 mypy 步驟設為 `continue-on-error: true`，錯誤會持續累積，strict 設定形同虛設。

## What Changes

- 修正現有 10 個 mypy 錯誤。
- CI 的 mypy 步驟移除 `continue-on-error`，改為必須通過。

## Capabilities

### New Capabilities
- `ci-pipeline`: 型別檢查為 CI 必要關卡。

### Modified Capabilities
（無）

## Impact

- `backend/app/services/line_service.py`、`backend/app/services/gcs_service.py`、`backend/pyproject.toml`
- `.github/workflows/ci.yml`
