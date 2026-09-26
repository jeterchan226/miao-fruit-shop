## ADDED Requirements

### Requirement: 訂單編號衝突時重試
系統 SHALL 在寫入訂單時若 `order_no` 與既有訂單衝突，重新產生編號並重試，最多 5 次；重試期間 MUST 保留已取得的規格鎖與庫存扣減。

#### Scenario: 第一次產生的編號已存在
- **WHEN** 編號產生器第一次回傳已存在的 `MM-AAAAAA`，第二次回傳新編號
- **THEN** 訂單以第二個編號成立，回應 201

#### Scenario: 重試耗盡
- **WHEN** 編號產生器連續 5 次回傳已存在的編號
- **THEN** 回應 503 `ORDER_NO_UNAVAILABLE`，不建立訂單，庫存不變
