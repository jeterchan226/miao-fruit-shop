## Context

`cli.py` 也直接使用 repositories，但 CLI 是與 routes 同層的「入口」，且 CLAUDE.md 的規則是針對 routes；本 change 不處理 CLI。

## Goals / Non-Goals

**Goals:** 修正唯一的違規；讓規則可自動檢查。

**Non-Goals:** 不引入 `import-linter` 等新工具；不重構 `cli.py`。

## Decisions

- **自寫 AST 測試，而非 `import-linter`**：規則只有兩條，AST 掃描（`ast.Import`、`ast.ImportFrom`）約 30 行即可，不必新增相依與設定檔。
- `get_active_admin` 接收 token 字串，讓 `decode_access_token` 的呼叫也移入 service，`deps.py` 只剩 FastAPI 依賴組裝。

## Risks / Trade-offs

- [AST 測試無法偵測 `importlib` 動態 import] → 專案沒有這種用法，可接受。
