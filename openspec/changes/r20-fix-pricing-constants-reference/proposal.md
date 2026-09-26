## Why

審查 #20：`backend/app/core/constants.py` 的註解寫「與前端 frontend/src/Cart.jsx 對齊」，但前端運費規則早已搬到 `frontend/src/pricing.js`。註解過期會誤導修改者去錯的檔案；更根本的問題是前後端兩份常數沒有任何自動檢查，一旦只改一邊，前台顯示金額與後端不同，所有訂單都會觸發 409 `PRICE_CHANGED`。

## What Changes

- 修正註解指向 `frontend/src/pricing.js`。
- 新增前後端一致性測試：pytest 解析 `pricing.js` 的 `FREE_SHIPPING`、`SHIPPING_BY_LAYER`，與後端常數比對。
- 新增雙向金額案例測試：同一組案例（小計、層數 → 運費）分別在 pytest 與 vitest 執行，案例存於共用 JSON。

## Capabilities

### New Capabilities
- `pricing-rules`: 前後端運費規則的一致性保證。

### Modified Capabilities
（無）

## Impact

- `backend/app/core/constants.py`
- 新增 `shared/pricing-cases.json`、`backend/tests/test_pricing_parity.py`
- `frontend/src/pricing.test.js` 讀取共用案例
