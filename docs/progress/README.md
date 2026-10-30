# 開發進度記憶（docs/progress）

跨 session 的開發記憶。每個 ticket 開發完（或中途停下）都要寫進這裡，下一個 session 從這裡接手，不靠對話紀錄。

## 結構

```
docs/progress/
├── README.md          本檔：格式與規則
├── STATUS.md          全域快照：系統現況、已完成 ticket、留待之後、下一步
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
| ticket 完成、開 PR 前 | `/work-on-ticket` | 狀態填 `完成`，補齊各段；更新 `STATUS.md`；與程式碼同一個 PR |
| PR review 修正後 | `/review-and-fix` | 在 `tickets/NN-*.md` 的「Review」段追加結果 |

`STATUS.md` 只在 ticket 完成時改，所以 master 上出現的每一列都代表已合併。進行中的狀態只存在 feature branch 的 ticket 紀錄裡。

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
- 範圍外發現的問題、重構機會（同步列入 STATUS.md）。

## 下一步
- 狀態非「完成」時必填：下一個 session 該從哪裡接手、卡在什麼。

## Review
- （由 /review-and-fix 追加）
```

## 規則

- 用繁體中文；程式碼、指令、路徑維持原文。
- 不複製 diff 或 spec 內容，用連結指過去。
- 「留待之後」解決時，從 `STATUS.md` 移除並註明解決的 ticket。
- rebase 時 `STATUS.md` 衝突：兩邊的列都保留，按 ticket 號碼排序。
