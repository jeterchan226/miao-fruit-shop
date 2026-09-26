## Why

審查 #19：LINE「購買須知」回覆（`PURCHASE_NOTICE_REPLY`）把運費「一層 $100／二層 $150／三層 $180」與免運門檻「NT$3,000」寫成字串，與 `core/constants.py` 的 `SHIPPING_BY_LAYER`、`FREE_SHIPPING_THRESHOLD` 是兩份來源；日後調整運費時，LINE 回覆會與實際計費不一致。銀行帳號、戶名等店家資訊也散落在 `line_service.py` 中。

## What Changes

- 購買須知文字改由 `build_purchase_notice()` 依 constants 動態組成。
- 店家匯款資訊（銀行、分行、戶名、帳號）與付款期限（3 日）集中到 `core/constants.py` 的 `StoreInfo`；Flex 訊息與文字摘要共用同一份。
- 回覆文字內容不變（僅來源改變）。

## Capabilities

### New Capabilities
- `line-notification`: LINE 訊息中的店家與運費資訊來源。

### Modified Capabilities
（無）

## Impact

- `backend/app/services/line_service.py`、`backend/app/core/constants.py`
- 測試：`tests/test_line_service.py`、`tests/test_line_webhook_service.py`
