## 1. 常數模組

- [ ] 1.1 新增 `frontend/src/constants.test.js`，斷言 `ORDER_SOURCE_STOREFRONT`、`ORDER_SOURCE_ADMIN`、`PAYMENT_METHOD_TRANSFER` 的值，確認因模組不存在而失敗
- [ ] 1.2 新增 `frontend/src/constants.js`（檔頭註明值須與 `backend/app/core/constants.py` 一致），確認 1.1 通過

## 2. 新訂單提醒改用常數

- [ ] 2.1 確認 `notifications.test.js` 現況通過，本票不修改此檔
- [ ] 2.2 `notifications.js` 的 `isCustomerOrder` 改引用 `ORDER_SOURCE_ADMIN`，確認 `notifications.test.js` 仍通過

## 3. 後台介面與顧客送單改用常數

- [ ] 3.1 `AdminApp.jsx` 的 `SOURCE_OPTIONS` 與 `SourceBadge` 改引用訂單來源常數，「全部」的空字串維持原樣
- [ ] 3.2 `Cart.jsx` 的 `buildOrderPayload` 改引用 `PAYMENT_METHOD_TRANSFER`

## 4. 驗證

- [ ] 4.1 `npm run test`
- [ ] 4.2 `npm run build`
- [ ] 4.3 搜尋 `frontend/src` 非測試檔，確認除 `constants.js` 外無 `'storefront'`、`'admin'`、`'transfer'` 字串常值
