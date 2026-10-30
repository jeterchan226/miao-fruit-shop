# 開發進度記憶（docs/progress）

跨 session 的開發記憶。每個 ticket 開發完（或中途停下）都要寫進這裡，下一個 session 從這裡接手，不靠對話紀錄。

## 結構

```
docs/progress/
├── README.md          本檔：格式與規則
├── STATUS.md          全域快照：部署待辦、系統現況、已完成 ticket、留待之後（自動產生，勿手改）
└── tickets/
    └── NN-<change-id>.md   單一 ticket 的開發紀錄（NN = GitHub issue 號碼，change-id = OpenSpec change 名稱）
```

三者分工：

- **GitHub issue**：要做什麼（目標、驗收條件），由 `/to-spec` 建立。
- **OpenSpec change**（`openspec/changes/<change-id>/`）：怎麼做（proposal、design、specs、tasks）。archive 後需求併入 `openspec/specs/`，成為系統現行規格。
- **docs/progress**：做到哪、做了什麼決定、留下什麼。只記 git log 與 OpenSpec 看不出來的東西。

## 誰寫、何時寫

| 時機 | 寫入者 | 動作 |
|---|---|---|
| ticket 開始 | `/work-on-ticket` | 讀 `STATUS.md`；若 `tickets/NN-*.md` 已存在（之前中斷過），從它的「下一步」接手 |
| ticket 中途停下（阻塞、需使用者決定、session 結束） | `/work-on-ticket` | 寫／更新 `tickets/NN-*.md`，狀態填 `進行中` 或 `阻塞`，提交到 feature branch |
| ticket 完成、開 PR 前 | `/work-on-ticket` | 狀態填 `完成`，補齊各段；與程式碼同一個 PR |
| PR review 修正後 | `/review-and-fix` | 在 `tickets/NN-*.md` 的「Review」段追加結果，deferred 項目寫進「留待之後」 |
| PR 合併進 `dev` | GitHub Action | 重新產生 `STATUS.md`，內容有變才由 bot commit 回 `dev` |
| 手動部署完成 | 部署者 | 刪除該 ticket 紀錄的「部署待辦」段並 commit |

## STATUS.md 如何產生

`scripts/generate_status.py` 每次從全部 ticket 紀錄與追蹤 issue 的狀態完整重建，PR 不改此檔，平行合併因此不衝突。

- 只有狀態為 `完成` 的紀錄會進快照；`進行中`、`阻塞` 的紀錄不列出。
- 系統現況只列最近三張有內容的 ticket。
- 追蹤 issue 關閉後，「留待之後」的項目自動消失；沒標追蹤 issue 的項目要從 ticket 紀錄刪除才會消失。
- 無法取得完整資料（ticket 紀錄格式不符、查不到 issue 狀態）時，script 以非零結束，保留現有快照，下一次合併補回。
- 直接 push 到 `dev` 不觸發更新，例如沒走 PR 的刪段 commit；等下一次合併，或本機產生後 commit。

本機產生（有 `GITHUB_TOKEN` 才帶上，沒有則匿名查詢）：

```bash
python3 scripts/generate_status.py
```

python.org 版 Python 報 `CERTIFICATE_VERIFY_FAILED` 時，前面加 `SSL_CERT_FILE=/etc/ssl/cert.pem`。

## tickets/NN-<change-id>.md 格式

```markdown
# #NN <ticket 標題>

- 狀態：完成 | 進行中 | 阻塞
- OpenSpec change：`<change-id>`（archive 後：`openspec/changes/archive/<YYYY-MM-DD>-<change-id>/`）
- Branch：`<branch>`
- 最後更新：YYYY-MM-DD

## 做了什麼
- 使用者看得到的變更，一行一項。

## 決定與偏離
- 開發中做的決定、與 spec 不同之處，以及原因。已寫進 ADR / GLOSSARY / design.md 的，附連結即可。

## 驗收結果
- [x] <Requirement / Scenario 名稱>：<自動測試名稱或手動驗證方式>
- [ ] <未通過者>：<原因>

## 留待之後
- 範圍外發現的問題、重構機會。有追蹤 issue 時在行尾標：#NN

## 系統現況
- 1–3 句，本 ticket 完成後系統的能力。純重構或無系統變化時可省略此段。

## 部署待辦
- 需手動執行的部署步驟。部署完刪除此段並 commit。

## 下一步
- 狀態非「完成」時必填：下一個 session 該從哪裡接手、卡在什麼。

## Review
- （由 /review-and-fix 追加）
```

`STATUS.md` 依下列欄位解析，格式不符會讓產生失敗：

- 標題 `# #NN <標題>`、`狀態`、`OpenSpec change`、`最後更新` 皆為必要。「最後更新」同時是已完成表格的完成日。
- 段落內只收頂層 `- ` 行，續行、子項目、註解不進快照。
- 只有行尾的 `：#NN`（可接句點）算追蹤 issue，內文提到的 `PR #76`、`可併入 #45` 不算。
- 去掉 `- ` 後為空、`無`、`無。` 視為沒有內容。

## 規則

- 用繁體中文；程式碼、指令、路徑維持原文。
- 不複製 diff 或 spec 內容，用連結指過去。
- 不手改 `STATUS.md`，要改內容就改 ticket 紀錄。
