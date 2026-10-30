# progress-status Specification

## Purpose
TBD - created by archiving change auto-generate-progress-status. Update Purpose after archive.
## Requirements
### Requirement: 合併後自動更新進度快照

PR 合併進 `dev` 後，系統 SHALL 依 `dev` 最新內容重新產生進度快照，內容有變時由 bot commit 回 `dev`。

#### Scenario: 合併到 dev 後更新
- **WHEN** PR 合併進 `dev`，且重新產生的快照與現有快照不同
- **THEN** bot 將新快照 commit 回 `dev`

#### Scenario: 內容無變化時不提交
- **WHEN** PR 合併進 `dev`，且重新產生的快照與現有快照相同
- **THEN** `dev` 不多出 commit

#### Scenario: 合併到其他分支不更新
- **WHEN** PR 合併進 `dev` 以外的分支
- **THEN** 不產生快照，也沒有 bot commit

#### Scenario: 自動提交不再觸發更新
- **WHEN** bot 將新快照 commit 回 `dev`
- **THEN** 該 commit 不再觸發一次快照更新

### Requirement: 平行 PR 不因進度快照衝突

PR MUST NOT 修改進度快照；快照只由自動更新寫入，所以平行的 PR SHALL 不會在此檔衝突。

#### Scenario: 兩個平行 PR 先後合併
- **WHEN** 兩個從同一基準開出的 PR 各自新增 ticket 紀錄，先後合併進 `dev`
- **THEN** 兩者都不因進度快照衝突，最後的快照同時列出這兩張 ticket

### Requirement: 已完成區塊

快照的「已完成」區塊 SHALL 列出狀態為完成的 ticket 紀錄的編號、標題、OpenSpec change、完成日與紀錄連結，依 ticket 編號遞增排序。完成日取自紀錄的最後更新日期。

#### Scenario: 完成的 ticket
- **WHEN** ticket 紀錄的狀態為完成
- **THEN** 「已完成」列出該 ticket 的編號、標題、OpenSpec change、完成日與紀錄連結

#### Scenario: 未完成的 ticket
- **WHEN** ticket 紀錄的狀態為進行中或阻塞
- **THEN** 快照的任何區塊都不列出該 ticket 的內容

### Requirement: 留待之後區塊

快照的「留待之後」區塊 SHALL 列出各 ticket 紀錄的「留待之後」項目與其來源 ticket。項目可在行尾標一個追蹤 issue；追蹤 issue 已關閉的項目 MUST NOT 列出。未標追蹤 issue 的項目 SHALL 持續列出，直到從 ticket 紀錄刪除。行尾以外提到的 issue 或 PR 編號不算追蹤 issue。

#### Scenario: 追蹤 issue 未關閉
- **WHEN** 「留待之後」項目標了追蹤 issue，且該 issue 未關閉
- **THEN** 快照列出該項目、來源 ticket 與追蹤 issue

#### Scenario: 追蹤 issue 已關閉
- **WHEN** 「留待之後」項目標了追蹤 issue，且該 issue 已關閉
- **THEN** 快照不列出該項目

#### Scenario: 未標追蹤 issue
- **WHEN** 「留待之後」項目未標追蹤 issue，內文提到其他 PR 編號
- **THEN** 快照列出該項目，不查該編號的狀態

### Requirement: 系統現況區塊

快照的「系統現況」區塊 SHALL 只列最近三張有「系統現況」內容的 ticket，依最後更新日期由新到舊，同日依 ticket 編號由大到小，並標明來源 ticket。

#### Scenario: 超過三張 ticket 有系統現況
- **WHEN** 四張 ticket 紀錄都有「系統現況」內容
- **THEN** 快照只列最近的三張，最舊的一張不列出

#### Scenario: 沒有系統現況內容的 ticket
- **WHEN** 最新的 ticket 紀錄沒有「系統現況」段，或該段為空
- **THEN** 該 ticket 不佔名額，快照改列下一張有內容的 ticket

### Requirement: 部署待辦區塊

快照的「部署待辦」區塊 SHALL 列出各 ticket 紀錄「部署待辦」段的項目與其來源 ticket。部署為手動，系統不判斷部署是否完成；項目 SHALL 在從 ticket 紀錄刪除之後的下一次產生時消失。

#### Scenario: 有部署待辦
- **WHEN** ticket 紀錄有「部署待辦」段
- **THEN** 快照列出其項目與來源 ticket

#### Scenario: 部署待辦從 ticket 紀錄刪除
- **WHEN** 「部署待辦」段從 ticket 紀錄刪除後重新產生快照
- **THEN** 快照不再顯示該項目

### Requirement: 不列下一步建議

快照 MUST NOT 包含「下一步建議」區塊。

#### Scenario: 產生的快照
- **WHEN** 產生快照
- **THEN** 內容沒有「下一步建議」區塊

### Requirement: 本機可重現

快照 SHALL 只取決於 ticket 紀錄與 issue 狀態，不含產生時間等隨執行環境變動的內容，所以手動執行 SHALL 與自動更新得到相同結果。

#### Scenario: 本機手動產生
- **WHEN** 在與 `dev` 相同內容的本機 checkout 手動執行產生指令，且 issue 狀態未變
- **THEN** 結果與 `dev` 上的快照完全相同

### Requirement: 無法產生時保留現有快照

無法取得完整資料時，產生 MUST 失敗並保留現有快照，不寫入部分結果，也不提交。

#### Scenario: 查不到 issue 狀態
- **WHEN** 產生時無法取得某個追蹤 issue 的狀態
- **THEN** 產生以非零結束，現有快照不變

#### Scenario: ticket 紀錄格式不符
- **WHEN** 某張 ticket 紀錄缺少標題、狀態、OpenSpec change 或最後更新
- **THEN** 產生以非零結束，錯誤訊息指出該檔案，現有快照不變

### Requirement: 既有進度遷移

啟用自動產生時，既有快照的資訊 SHALL 遷移進 ticket 紀錄，「下一步建議」以外的資訊 MUST NOT 遺失。

#### Scenario: 遷移後第一次產生
- **WHEN** 遷移完成後產生快照，且「留待之後」的追蹤 issue 皆未關閉
- **THEN** 遷移前的系統現況、已完成與留待之後資訊都仍在快照中，待部署的 #46 列於「部署待辦」

