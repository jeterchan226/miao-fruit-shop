## MODIFIED Requirements

### Requirement: 金額以後端計算為準

系統 MUST 在成立訂單或修改訂單品項時，以後端計算的訂單合計核對請求的 `expected_total`；不一致時 SHALL 回傳 409 `PRICE_CHANGED` 並附上商品小計、運費、手續費與訂單合計，且不寫入任何變更。計算時，新的訂單品項 SHALL 採用規格目前的價格與包裝類型，既有訂單品項 SHALL 採用成立時固定的下單價與包裝類型。

#### Scenario: 顧客下單金額不符

- **WHEN** 顧客下單的 `expected_total` 與後端計算不一致
- **THEN** 系統回傳 409 `PRICE_CHANGED` 與新的金額，訂單未成立、庫存不變

#### Scenario: 代客下單金額不符

- **WHEN** 代客下單的 `expected_total` 與後端計算不一致
- **THEN** 系統回傳 409 `PRICE_CHANGED`，訂單未成立、庫存不變

#### Scenario: 修改訂單品項金額不符

- **WHEN** 修改訂單品項的 `expected_total` 與後端計算不一致
- **THEN** 系統回傳 409 `PRICE_CHANGED`，訂單與庫存不變

#### Scenario: 修改訂單品項時規格已調價且改包裝類型

- **WHEN** 訂單成立後規格調價並改包裝類型，管理員修改該訂單時新增另一個規格
- **THEN** 既有訂單品項以下單價與快照的包裝類型計算，新訂單品項以規格目前的價格與包裝類型計算，訂單合計為兩者加總後的結果
