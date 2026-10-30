Ticket: #87

## Why

每個 PR 都手改進度快照的同一段，平行開發時先合併一個，其餘全部衝突（PR #76、#77 在 PR #78 合併後都撞此檔）；平行派工後每輪都會發生。快照內容大多已存在於 ticket 紀錄與 GitHub issue，手動維護是重複的。

## What Changes

- 進度快照改為由 ticket 紀錄與 GitHub issue 狀態產生：PR 只寫 ticket 紀錄，不再手改快照。
- PR 合併進 `dev` 後，GitHub Action 重新產生快照，內容有變才由 bot commit 回 `dev`。
- ticket 紀錄新增「系統現況」「部署待辦」兩段，「留待之後」的項目可標追蹤 issue。
- 快照新增「部署待辦」區塊，刪除「下一步建議」區塊（改看 GitHub board 與 `/orchestrator`）。
- 更新 `/work-on-ticket`、`/review-and-fix` 與進度紀錄規則：不再改快照，也不用解它的衝突。
- 既有快照內容遷移進 ticket 紀錄。

## User Stories

1. 身為開發者，我想要平行的 PR 不再因進度快照衝突，以便先後合併時不必逐一 rebase 解衝突。
2. 身為新開的 session，我想要讀到自動更新的進度快照，以便快速理解專案進度，不必翻每張 ticket 紀錄。
3. 身為店家維運者，我想要在快照看到待部署的事項，並在部署後刪掉它，以便知道還有什麼沒上線。
4. 身為開發者，我想要已解決的「留待之後」自動消失，以便快照只列仍待處理的事。
5. 身為開發者，我想要在本機手動跑出相同的快照，以便不合併也能檢查結果。

## Capabilities

### New Capabilities

- `progress-status`: 進度快照的產生來源、區塊內容、自動更新時機與失敗行為。

### Modified Capabilities

無。

## Impact

- 新增一支產生快照的 Python script 與其單元測試（僅用標準函式庫，無新相依）。
- GitHub Actions：既有的 dev 合併 workflow 新增產生快照的 job；CI 新增跑該測試的 job。
- 開發流程文件：`/work-on-ticket`、`/review-and-fix` skill、進度紀錄 README、專案 CLAUDE.md。
- 既有 ticket 紀錄與進度快照的內容遷移。
- 不影響商店、後台與 API。
