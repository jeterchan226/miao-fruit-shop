## Context

錯誤清單：`line_service.py:97,107,121,134,135,154,185,192` 為 `dict` 缺型別參數；`gcs_service.py:6` 為 `google.cloud` 無 `py.typed`；`gcs_service.py:29` 為呼叫未型別化的 `from_service_account_info`。

## Goals / Non-Goals

**Goals:** mypy 零錯誤並在 CI 強制。

**Non-Goals:** 不為 google-cloud 撰寫完整 stub。

## Decisions

- Flex 訊息的 dict 使用型別別名 `FlexJson = dict[str, Any]`，比 `TypedDict` 精簡；Flex 結構由 LINE SDK 的 `FlexContainer.from_dict` 在執行期驗證。
- `google.cloud.*`、`google.oauth2.*` 在 `pyproject.toml` 加 `[[tool.mypy.overrides]] ignore_missing_imports = true`；`from_service_account_info` 的呼叫處加上精確的 `# type: ignore[no-untyped-call]`，而非放寬整個模組。
- 「測試」即為 mypy 本身：TDD 的紅燈是先把 CI 改為必要（確認失敗），再修正。

## Risks / Trade-offs

- [其他進行中的分支合併後帶入新 mypy 錯誤而擋住 CI] → 在合併本 change 前先公告；錯誤數少，修正成本低。
