# #87 合併到 dev 後由 GitHub Action 自動產生 docs/progress/STATUS.md

- 狀態：完成
- OpenSpec change：`auto-generate-progress-status`（archive 後：`openspec/changes/archive/2026-10-30-auto-generate-progress-status/`）
- Branch：`claude/zealous-gates-ddaec3`
- 最後更新：2026-10-30

## 做了什麼
- `STATUS.md` 改由 `scripts/generate_status.py` 從 ticket 紀錄與 issue 狀態產生，PR 不再手改。
- PR 合併進 `dev` 後，Action 重新產生快照，內容有變才由 bot commit 回 `dev`。
- 快照新增「部署待辦」，刪除「下一步建議」；ticket 紀錄新增「系統現況」「部署待辦」段。
- `/work-on-ticket`、`/review-and-fix`、`docs/progress/README.md`、`CLAUDE.md` 改為新流程。

## 決定與偏離
- 遷移驗證（task 5.1）用 scratchpad 的一次性 script，未提交：對實際紀錄斷言「#46 在部署待辦」，部署後刪段就會讓 CI 紅燈。比對項目為遷移前的已完成每一列、追蹤 issue 與併回的備註。
- 只收段內頂層 `- ` 行：續行、子項目、註解不進快照，否則會變成永久列出的項目。
- 多擋不合法的狀態值，與缺欄位同樣以非零結束。
- 表格格內的 `|` 跳脫，避免破壞表格。
- #67 紀錄標題移除 `refactor: `，讓「已完成」列與遷移前相同。本紀錄標題同樣不含 `chore: `。
- 本紀錄不寫「系統現況」：只改開發流程，系統能力沒變，且寫了會擠掉 #31 的現況。
- 本 PR 仍提交重新產生的 `STATUS.md`（design.md Migration Plan）。
- 本機 python.org 版 Python 無 CA bundle，以 `SSL_CERT_FILE=/etc/ssl/cert.pem` 執行，已寫進 README。

## 驗收結果
- [ ] 合併後自動更新進度快照 — 合併到 dev 後更新：合併後才能驗證
- [ ] 合併後自動更新進度快照 — 內容無變化時不提交：合併後才能驗證；`git diff --quiet` 邏輯人工檢視
- [x] 合併後自動更新進度快照 — 合併到其他分支不更新：workflow 觸發條件 `branches: [dev]`，人工檢視
- [ ] 合併後自動更新進度快照 — 自動提交不再觸發更新：合併後才能驗證；觸發事件只有 `pull_request: closed`
- [x] 平行 PR 不因進度快照衝突 — 兩個平行 PR 先後合併：`git merge-tree` 模擬兩條各新增 ticket 紀錄的分支，無衝突；`test_lists_done_tickets_by_number`
- [x] 已完成區塊 — 完成的 ticket：`test_lists_done_tickets_by_number`
- [x] 已完成區塊 — 未完成的 ticket：`test_unfinished_tickets_appear_nowhere`
- [x] 留待之後區塊 — 追蹤 issue 未關閉：`test_closed_tracking_issue_is_hidden`
- [x] 留待之後區塊 — 追蹤 issue 已關閉：`test_closed_tracking_issue_is_hidden`
- [x] 留待之後區塊 — 未標追蹤 issue：`test_untracked_item_stays_with_placeholder`、`test_only_line_end_marker_is_a_tracking_issue`
- [x] 系統現況區塊 — 超過三張 ticket 有系統現況：`test_only_three_most_recent`
- [x] 系統現況區塊 — 沒有系統現況內容的 ticket：`test_ticket_without_content_takes_no_slot`
- [x] 部署待辦區塊 — 有部署待辦：`test_lists_items_with_source_ticket`
- [x] 部署待辦區塊 — 部署待辦從 ticket 紀錄刪除：`test_removed_section_disappears`
- [x] 不列下一步建議 — 產生的快照：`test_section_order_and_no_next_step_section`
- [x] 本機可重現 — 本機手動產生：`test_same_input_same_output`；本機連跑兩次輸出相同
- [x] 無法產生時保留現有快照 — 查不到 issue 狀態：`test_issue_lookup_failure_keeps_snapshot`；本機實際遇 SSL 失敗，exit 1，檔案不變
- [x] 無法產生時保留現有快照 — ticket 紀錄格式不符：`test_malformed_ticket_keeps_snapshot_and_names_file`、`test_missing_required_field_names_the_file`
- [x] 既有進度遷移 — 遷移後第一次產生：一次性 script 比對通過（見上），並人工比對遷移前後

## 留待之後
- 合併後確認第一次 Action run 成功、bot commit 後無新 run，勾選 #87 剩餘三條驗收並刪除本項（task 8.6）。
- bot push 沒有 rebase 或重試：checkout 到 push 之間有人直接 push 到 `dev` 時 job 失敗，下一次合併補回。
- `Closes` 指向不存在的 issue 時 close-issues 失敗，generate-status 被跳過，下一次合併補回。
- `scripts/` 不在 ruff、mypy 範圍內。
- 系統現況的純重構內容佔三格之一，例如 #67。
- 在途舊流程 PR（#29、#43、#60 的 PR）內容只在 `STATUS.md` 的部分要搬進各自紀錄，含 #29 的部署順序，否則快照漏列。
- 行尾寫成 `追蹤於 #NN。` 不算追蹤 issue，不會報錯，項目永久列出（#43 紀錄目前如此）。

## 下一步
- 無。

## Review
- 2026-10-30 `/review-and-fix`，範圍 `3ee4204..d8bffe5`：13 項，auto-fix 4、needs-decision 6、rejected 3、deferred 0。第 3 項：tasks 8.4 寫「由 CI 確認」，但 CI 沒有 ruff；本機補跑 backend ruff、mypy、pytest 皆通過。
- Needs decision：完成狀態過濾重複、表格組裝重複、區塊名稱字串散落、狀態未用 Enum、「PR MUST NOT 修改快照」無機制強制且在途 PR 有資料遺失風險、行尾 `追蹤於 #NN` 靜默不算追蹤。
