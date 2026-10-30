## 1. 非字串 detail 正規化

- [ ] 1.1 新增失敗測試 `frontend/src/apiError.test.js`：物件陣列、物件、空陣列的 `detail` 轉為固定訊息，`err.message` 為字串，傳入的 `data` 未被修改
- [ ] 1.2 建立 `frontend/src/apiError.js`，把 `ApiError` 從 `api.js` 移入並實作正規化
- [ ] 1.3 `api.js` 匯入並重新匯出 `ApiError`，`window.MiaoApi` 內容不變

## 2. 既有行為不變

- [ ] 2.1 新增測試：字串 `detail` 原樣保留，無 `detail` 與 `null` 維持 falsy，`code` 與其他欄位保留
- [ ] 2.2 確認測試通過，必要時調整實作

## 3. 驗證

- [ ] 3.1 `npm test` 與 `npm run build` 通過
- [ ] 3.2 本機啟動前後端，手動確認空白登入與規格小數售價顯示固定訊息，畫面未崩潰
- [ ] 3.3 手動確認業務錯誤（如刪除或狀態轉移失敗）仍顯示原文
