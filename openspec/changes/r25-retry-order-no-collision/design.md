## Context

`create_order` 在同一交易中持有規格鎖並扣庫存後才 insert 訂單。若 insert 失敗且整個交易 rollback，庫存扣減會一起還原（正確），但使用者得到 500。

## Goals / Non-Goals

**Goals:** 衝突時自動恢復；重試耗盡時回可理解的錯誤。

**Non-Goals:** 不改編號格式或長度。

## Decisions

- **以 `session.begin_nested()`（SAVEPOINT）包住 insert**：衝突時只 rollback 到 savepoint，保留外層交易中的規格鎖與扣減，不需重新驗證。替代方案「整個交易重做」會釋放鎖、需重跑所有驗證。
- 捕捉 `IntegrityError` 後檢查 `orig.sqlstate == "23505"` 且 constraint 名稱為 `order_no` 的 unique index，其他完整性錯誤照常拋出。
- 編號產生函式可注入（參數預設 `_new_order_no`），讓測試能強制產生衝突。

## Risks / Trade-offs

- [測試用的 `db_session` 已使用 `join_transaction_mode="create_savepoint"`] → 巢狀 savepoint 在 Postgres 支援，需以測試確認 fixture 相容。
