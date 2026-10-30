## 1. 解析 ticket 紀錄

- [ ] 1.1 寫失敗測試：`parse_ticket` 取出編號、標題、狀態、change、最後更新與各段內容；缺必要欄位時報錯並指出檔名
- [ ] 1.2 寫失敗測試：「留待之後」行尾 `：#NN` 才算追蹤 issue，`PR #76`、`可併入 #45` 不算；空內容（`- `、`無`、`無。`）視為沒有內容
- [ ] 1.3 實作 `parse_ticket`，測試轉綠

## 2. 產生已完成與留待之後

- [ ] 2.1 寫失敗測試：已完成列出完成的 ticket 並依編號排序；進行中、阻塞的 ticket 不出現在任何區塊
- [ ] 2.2 寫失敗測試：留待之後的追蹤 issue 已關閉時不列出、未關閉時列出、未標時持續列出
- [ ] 2.3 寫失敗測試：輸出不含「下一步建議」，不含時間戳，同樣輸入得到相同輸出
- [ ] 2.4 實作 `render_status` 的版面、已完成與留待之後，測試轉綠

## 3. 系統現況與部署待辦

- [ ] 3.1 寫失敗測試：系統現況只列最近三張，排序依日期、編號；沒有內容的 ticket 不佔名額
- [ ] 3.2 寫失敗測試：部署待辦列出項目與來源 ticket；段落刪除後不再顯示
- [ ] 3.3 實作兩個區塊，測試轉綠

## 4. 命令列與失敗行為

- [ ] 4.1 寫失敗測試：查 issue 失敗、ticket 格式不符時以非零結束，現有 `STATUS.md` 不變
- [ ] 4.2 實作 `main()`：讀 ticket 紀錄、查追蹤 issue（有 `GITHUB_TOKEN` 才帶）、寫檔，測試轉綠
- [ ] 4.3 在 `.github/workflows/ci.yml` 新增跑 `python3 -m unittest discover -s scripts` 的 `scripts` job（Python 3.13）

## 5. 遷移既有進度

- [ ] 5.1 寫失敗測試：對 repo 內實際的 ticket 紀錄產生快照，遷移前 `STATUS.md` 的系統現況、已完成、留待之後資訊皆在，#46 列於部署待辦
- [ ] 5.2 依 design.md D7 更新 #31、#46、#67 的 ticket 紀錄，測試轉綠
- [ ] 5.3 執行 script 產生新的 `STATUS.md`，人工比對遷移前後

## 6. 自動更新 workflow

- [ ] 6.1 在 `close-issues-on-dev.yml` 新增 `generate-status` job，依 design.md D2（`needs`、`ref: dev`、權限、`concurrency`、無變化不提交），更新 workflow `name`
- [ ] 6.2 檢查 workflow YAML（`actionlint` 或人工），確認觸發只有 `pull_request: closed` 且 `branches: [dev]`

## 7. 流程文件

- [ ] 7.1 更新 `.claude/skills/work-on-ticket/SKILL.md` 第 6、8 步
- [ ] 7.2 更新 `.claude/skills/review-and-fix/SKILL.md` 第 6 步
- [ ] 7.3 更新 `docs/progress/README.md`：結構、誰寫何時寫、格式、規則、手動部署後的流程、本機指令
- [ ] 7.4 更新根目錄 `CLAUDE.md` 的 Docs 段
- [ ] 7.5 搜尋 repo 內其他「手改 `STATUS.md`」的指示並修正

## 8. 驗證

- [ ] 8.1 `python3 -m unittest discover -s scripts` 全數通過
- [ ] 8.2 本機跑 script 兩次，輸出相同，且與提交的 `STATUS.md` 一致
- [ ] 8.3 用 `git merge-tree` 模擬兩條各新增 ticket 紀錄的分支，確認無衝突
- [ ] 8.4 `backend/` 的 ruff、mypy、pytest 與 `frontend/` 的 test、build 不受影響（本 ticket 未改動，由 CI 確認）
- [ ] 8.5 ticket 紀錄與 PR 註明合併後才能驗證的項目：自動 commit、不自我觸發
- [ ] 8.6 合併後確認第一次 Action run 成功，把結果補進 ticket 紀錄並勾選對應驗收條件
