## Context

`docs/progress/STATUS.md` 由每個 ticket 的 PR 手改，平行 PR 必定在同一段衝突。其內容大多已存在於 `docs/progress/tickets/NN-*.md` 與 GitHub issue。

現況與限制：

- `dev` 沒有 branch protection，bot 可直接 push。
- `.github/workflows/close-issues-on-dev.yml` 已用 `pull_request: closed`（`branches: [dev]`、`merged == true`）在合併時關閉 issue。
- 部署為手動（ADR 0002），系統無法得知部署完成。
- repo 是公開的，issue 狀態不帶 token 也查得到。
- CI 只跑 PR 與 master push，`dev` 上的 bot commit 不會觸發它。

## Goals / Non-Goals

**Goals:**

- PR 不再改 `STATUS.md`，平行合併不衝突。
- `STATUS.md` 維持「新 session 快速理解進度」的用途，由 ticket 紀錄與 issue 狀態完整重建。
- 本機與 Action 跑出相同結果。

**Non-Goals:**

- 自動判斷部署完成。
- issue 關閉或直接 push 到 `dev` 當下立刻更新快照（下一次合併時更新）。
- `workflow_dispatch` 手動觸發。
- 遷移 2026-10-30 以前、沒有 ticket 紀錄的工作。
- 改變 `master` 的部署流程；`STATUS.md` 隨 `dev` 合併進 `master`。

## Decisions

### D1. 產生器是 stdlib-only 的單一 script

`scripts/generate_status.py`，無第三方相依，每次從全部 ticket 紀錄完整重建，所以 idempotent，上一次失敗由下一次自動補回。拆成三段：`parse_ticket(filename, text)`、`render_status(tickets, closed_issues)`（兩者皆純函式）、`main()`（讀檔、查 issue、寫檔）。

選這個而不是放進 `backend/`：它與應用程式無關，不該依賴 `uv` 環境或 Postgres。

### D2. 接在 close-issues job 之後

在 `close-issues-on-dev.yml` 新增 `generate-status` job，`needs: close-issues`，並把 workflow `name` 改成涵蓋兩者。不用 `paths` 過濾，每次合併都跑，無變化就不 commit。

選這個而不是獨立 workflow 的 `push: dev`：獨立 workflow 會和 close-issues 競速，「關閉 #82 的 PR」產生快照時 #82 可能還沒關，已解決的項目要多留一輪。`workflow_run` 只讀預設分支（`master`）上的 workflow 檔，`dev` 上改了不生效，也不採用。

代價：直接 push 到 `dev` 不觸發，手動刪部署待辦的 commit 若沒走 PR，要等下一次合併。這與 ticket 的「下次產生即移除」一致。

job 要點：

- `actions/checkout` 指定 `ref: dev`。`pull_request` 事件預設 checkout 的是 merge ref，不是最新的 `dev`。
- job 層 `permissions: { contents: write, issues: read }`；close-issues 維持 workflow 層的 `issues: write`。
- 條件 `if: github.event.pull_request.merged == true`。
- `concurrency: { group: generate-status, cancel-in-progress: false }`，序列化連續合併，避免兩個 run 互相 push 失敗。排隊被取代的 run 不影響結果，因為後一個 run 讀到的 `dev` 已包含前者。
- `git diff --quiet -- docs/progress/STATUS.md` 無變化就結束；否則以 `github-actions[bot]` commit `docs: regenerate progress status` 後 push。

### D3. 不會自我觸發

觸發事件是 `pull_request: closed`，bot 直接 push 不產生 PR 事件；而且 `GITHUB_TOKEN` 推的 commit 本來就不觸發 workflow。不需要 `[skip ci]` 或 commit 訊息過濾。

### D4. ticket 紀錄格式

新增兩段，放在「留待之後」之後：

```markdown
## 系統現況
- 1–3 句，本 ticket 完成後系統的能力。純重構或無系統變化時可省略此段。

## 部署待辦
- 需手動執行的部署步驟。部署完刪除此段並 commit。
```

「留待之後」的項目以行尾 `：#NN` 標追蹤 issue，例如 `- 錯誤訊息改用快照名稱（可併入 #45）：#83`。解析用 `：#(\d+)。?$`，只看行尾，所以 `PR #76`、`可併入 #45` 不會被誤判。

空內容判定：去掉 `- ` 後為空、`無`、`無。` 視為沒有內容（既有紀錄有 `- 無。` 與空 `- `）。

### D5. 查 issue 狀態

只對有標追蹤 issue 的項目逐一 `GET /repos/jeterchan226/miao-fruit-shop/issues/{n}`，用 `urllib`，設 timeout；有 `GITHUB_TOKEN` 就帶上，沒有就匿名（本機用，repo 公開）。任何非 200 或網路錯誤都讓 script 以非零結束，不寫檔。

選這個而不是把查不到的項目當未關閉：靜默降級會讓快照默默失真，失敗可見且下次合併自動補回。

### D6. 快照版面

依序：開頭說明（標示自動產生、勿手改，保留「自 2026-10-30 起記錄」）、部署待辦、系統現況、已完成、留待之後。部署待辦放最前，因為它最需要被看見。區塊無內容時寫 `無。`，版面固定。

- 部署待辦：`- #NN：<項目>`。
- 系統現況：`**#NN**：<內容>`，最近三張，常數 `RECENT_TICKETS = 3`。
- 已完成：沿用現有表格欄位。
- 留待之後：表格 `項目 | 來源 ticket | 追蹤 issue`，依來源 ticket 編號、原順序排列，沒有追蹤 issue 的格子留 `—`。

輸出不含時間戳，以符合本機可重現。

### D7. 遷移內容

- 系統現況：三段分別寫進 #31、#46、#67 的紀錄。
- 部署待辦：#46 寫入「先跑 migration，立刻部署後端，再部署前端」。
- 留待之後：`STATUS.md` 表格的備註併回 ticket 紀錄對應行，追蹤 issue 改為行尾格式（#79、#80、#81、#82、#83、#84、#85）；「登入確認 PR #76 的 log」無追蹤 issue，持續列出。
- 下一步建議：依 ticket 刪除；其中 #46 部署已進部署待辦，Vercel log 已在留待之後，#82 已在留待之後。

### D8. 文件更新

- `.claude/skills/work-on-ticket/SKILL.md`：第 6 步改寫 ticket 紀錄（含「系統現況」「部署待辦」），不更新 `STATUS.md`；第 8 步移除 `STATUS.md` 衝突規則。讀 `STATUS.md` 的第 3 步不變。
- `.claude/skills/review-and-fix/SKILL.md` 第 6 步：deferred 項目寫進 ticket 紀錄的「留待之後」，行尾標新 issue。
- `docs/progress/README.md`：結構、誰寫何時寫、格式、規則全部更新，移除 `STATUS.md` 衝突規則，寫明手動部署後刪段的流程與本機指令。
- 根目錄 `CLAUDE.md` 的 Docs 段：註明 `STATUS.md` 為自動產生。

## Testing Decisions

**入口：純函式（`parse_ticket`、`render_status`）**，用 `unittest` 測，不打網路也不需要 DB。repo 既有四種入口中，這對應 pure domain function；這是能涵蓋全部內容規則的最高入口，HTTP API 與 DB 都不涉及。prior art：`backend/tests/test_order_amounts.py` 的 `compute_amounts` 純函式測試風格，`frontend/src/pricing.test.js` 的表格式案例。

- 測試檔 `scripts/test_generate_status.py`，以 inline 字串當 ticket 紀錄，`closed_issues` 傳 set，不 mock HTTP。
- `main()` 層補兩個測試：查 issue 失敗與格式不符時以非零結束且不改檔（用暫存目錄，注入會失敗的查詢函式）。
- 遷移驗證：對 repo 內實際的 ticket 紀錄跑 `render_status`，`closed_issues` 傳空 set，比對遷移前 `STATUS.md` 的每一列都還在（下一步建議除外）。
- CI 新增 `scripts` job，`python3 -m unittest discover -s scripts`，Python 3.13。放獨立 job 是因為現有 backend job 依賴 Postgres，frontend job 沒有 Python 環境需求。

**workflow 行為無法在 PR 上自動測試**，以人工方式驗證並記在 ticket 紀錄：

- 自動更新與「不自我觸發」：本 PR 合併本身就是第一次實測，合併後看 Actions run 與 `dev` log；bot commit 之後不應再有新 run。合併後才能勾的驗收項，在 PR 內註明。
- 平行不衝突：`git merge-tree` 模擬兩條各新增 ticket 紀錄的分支。
- 推上去前用 `actionlint` 檢查 workflow（環境有裝時），或人工檢視 YAML。

## Risks / Trade-offs

- [部署待辦須手動刪除，否則一直顯示] → README 寫明流程；該區塊放快照最前，顯眼。
- [手動刪段的 commit 沒走 PR，快照延後更新] → 接受；下次合併即更新，也可本機跑 script 後 commit。
- [`STATUS.md` 手改會被覆蓋] → 開頭標示自動產生；README 寫明。
- [進行中的舊流程 PR 仍改 `STATUS.md`] → 它們的修改會在下次產生時被覆蓋，資訊若只在 `STATUS.md` 就會遺失。此時已開的 PR 要把內容寫進 ticket 紀錄，並撤掉對 `STATUS.md` 的修改。
- [GitHub API 暫時失敗讓 job 紅燈] → 只影響快照新鮮度；下一次合併補回。
- [系統現況只取三張，較舊的現況會消失] → 依 ticket 要求；完整內容仍在 ticket 紀錄與 `openspec/specs/`。
- [`.claude/skills/` 可能不可寫] → ticket 說明 worktree 內可寫，但 sandbox 設定可能拒絕該路徑。若被擋，停下回報，不要繞過。
- [workflow 改名] → 只改 `name`，不改檔名與觸發條件；既有 run 紀錄不受影響。

## Migration Plan

1. 同一個 PR 內完成 script、測試、workflow、文件與 D7 的內容遷移，並提交重新產生的 `STATUS.md`。
2. 合併後確認第一次 Action run 成功，且 `STATUS.md` 無非預期變動。
3. 回退：revert 該 PR，`STATUS.md` 回到手動維護。
