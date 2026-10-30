## ADDED Requirements

### Requirement: 後台呈現非字串的錯誤內容

API 回應的 `detail` 不是字串時（例如框架驗證錯誤的物件陣列），後台 SHALL 顯示「資料格式有誤，請檢查輸入內容後再送出。」，MUST NOT 使畫面崩潰，也 MUST NOT 顯示原始驗證內容。`detail` 為字串時 SHALL 照原文顯示；回應沒有 `detail` 時 SHALL 顯示該操作原有的錯誤訊息。

#### Scenario: 登入帳密留白

- **WHEN** 管理員未填帳號與密碼就送出登入，API 回傳 422 與物件陣列的 `detail`
- **THEN** 登入畫面維持顯示，並顯示「資料格式有誤，請檢查輸入內容後再送出。」

#### Scenario: 規格售價填小數

- **WHEN** 管理員以小數售價儲存規格，API 回傳 422 與物件陣列的 `detail`
- **THEN** 規格表單維持顯示，並顯示「資料格式有誤，請檢查輸入內容後再送出。」

#### Scenario: 業務錯誤維持原文

- **WHEN** API 回傳字串 `detail` 的錯誤
- **THEN** 後台顯示該字串

#### Scenario: 回應沒有錯誤內容

- **WHEN** API 回傳的錯誤沒有 `detail`
- **THEN** 後台顯示該操作原有的錯誤訊息
