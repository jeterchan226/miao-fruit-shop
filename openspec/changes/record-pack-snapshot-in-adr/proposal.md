Ticket: #85

## Why

ADR 0003 寫後端「以規格現況重新計算」，ADR 0004 只固定下單價。#46 之後，既有訂單品項的包裝類型也固定在成立當下，層數與運費不再全讀規格現況。兩份 ADR 都沒記這項決定，照字面讀會以為運費該跟著規格走，之後改金額邏輯的人可能把 #46 的行為改回去。

## What Changes

- ADR 0004 補上：包裝類型與下單價同樣在訂單品項成立時固定，附上理由與否決的選項。
- ADR 0003 改寫重新計算的依據：新訂單品項讀規格現況，既有訂單品項讀成立時固定的下單價與包裝類型。
- `order-pricing` 的「金額以後端計算為準」寫明同一條金額基礎，並補一個情境。系統行為不變。

## User Stories

1. 身為之後修改金額邏輯的開發者，我想要從 ADR 讀到包裝類型也固定在訂單成立當下，以便不會把既有訂單的運費改回跟著規格現況計算。
2. 身為管理員，我想要後台編輯訂單時既有訂單品項的金額基礎維持不變，以便顧客已同意的金額不被規格改動影響。

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `order-pricing`: 「金額以後端計算為準」明定新舊訂單品項各自的金額基礎。

## Impact

- 文件：`docs/adr/0003-backend-is-source-of-truth-for-amounts.md`、`docs/adr/0004-order-price-fixed-at-submission.md`。
- 後端、前端 production 程式碼、API、資料庫皆不變。
- 測試：後台修改訂單品項的 API 測試多一個情境。
