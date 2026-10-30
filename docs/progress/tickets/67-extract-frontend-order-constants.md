# #67 refactor: 前端訂單來源、付款方式字串改用常數模組

- 狀態：完成
- OpenSpec change：`extract-frontend-order-constants`（archive 後：`openspec/changes/archive/2026-10-30-extract-frontend-order-constants/`）
- Branch：`claude/friendly-hawking-f1f827`
- 最後更新：2026-10-30

## 做了什麼
- 使用者看不到變更：純重構，畫面、API 請求內容與提醒行為不變。
- 新增 `frontend/src/constants.js`，`notifications.js`、`AdminApp.jsx`、`Cart.jsx` 改引用。

## 決定與偏離
- 無偏離，見 change 的 [design.md](../../../openspec/changes/archive/2026-10-30-extract-frontend-order-constants/design.md)。
- `PAYMENT_METHOD_LABELS` 的物件 key `transfer` 不在 design 列出的五處，維持原樣，列入留待之後。

## 驗收結果
- [x] 代客下單不提醒 — 新代客下單：`notifications.test.js`「只有代客下單 → 不計未讀」、「只多了代客下單 → 不響鈴」
- [x] 代客下單不提醒 — 顧客下單與代客下單同時出現：`notifications.test.js` 的「排除代客下單」混合來源案例
- [x] 後台列表介面的篩選對應 — 日期區間：`dateRange.test.js`
- [x] 後台列表介面的篩選對應 — 搜尋訂單編號：無自動測試；`resolveSearchParams` 本票未改，人工讀碼確認
- [x] 後台列表介面的篩選對應 — 搜尋其他文字：同上
- [x] 後台列表介面的篩選對應 — 依訂單來源選項篩選：`SOURCE_OPTIONS` 值由 `constants.test.js` 鎖定、後端 `test_admin_orders` 系列涵蓋 `source=admin`；介面無元件測試
- [x] 代客下單標籤 — 代客下單顯示標籤：無元件測試；`npm run build` 擋匯入錯誤、`constants.test.js` 鎖值、搜尋確認
- [x] 代客下單標籤 — 顧客下單不顯示標籤：同上
- [x] 顧客下單 — 下單成功：`test_create_order_201`、`test_create_order_source_is_storefront`
- [x] 顧客下單 — 公開回應不含後台欄位：後端本票未改；回應由 schema 欄位限定，人工讀碼確認，既有測試只斷言 `stock_qty`
- [x] 顧客下單 — 商店頁送出的付款方式：無元件測試；`npm run build` 擋匯入錯誤、`constants.test.js` 鎖值

未實際開瀏覽器操作；以上「無自動測試」項目依 design 的驗證方式處理。

## 留待之後
- `AdminApp.jsx` 的 `PAYMENT_METHOD_LABELS` 物件 key 仍手寫 `transfer`，可改 `[PAYMENT_METHOD_TRANSFER]`。
- 公開下單回應不含後台欄位缺明確的自動測試。

## 下一步

## Review
