# product-images Specification

## Purpose

描述管理員管理商品圖片的能力：取得直傳雲端儲存的簽章網址、登錄已上傳的圖片、依包裝類型維護相片組與排序，以及刪除圖片。商店頁如何使用這些圖片見 storefront-catalog。

## Requirements

### Requirement: 圖片 API 需管理員身分

系統 MUST 對所有後台圖片 API 要求有效的管理員 token，否則回傳 401。

#### Scenario: 未帶 token 取得簽章

- **WHEN** 未帶 token 請求上傳簽章
- **THEN** 系統回傳 401

### Requirement: 取得上傳簽章

系統 SHALL 依檔名與內容類型回傳上傳用簽章網址與上傳後的公開網址；內容類型僅接受 JPEG、PNG、WebP、GIF，其他類型回傳 422；雲端儲存未設定時回傳 400。

#### Scenario: 取得簽章

- **WHEN** 管理員以允許的內容類型請求簽章
- **THEN** 系統回傳 `signed_url` 與 `public_url`

#### Scenario: 不支援的內容類型

- **WHEN** 內容類型不在允許清單
- **THEN** 系統回傳 422

#### Scenario: 雲端儲存未設定

- **WHEN** 雲端儲存未設定時請求簽章
- **THEN** 系統回傳 400

### Requirement: 登錄圖片

系統 SHALL 允許管理員把已上傳的網址登錄為商品圖片並回傳 201，排序值預設 0；商品不存在時回傳 404，未定義的欄位回傳 422。

#### Scenario: 登錄成功

- **WHEN** 管理員登錄圖片網址
- **THEN** 系統回傳 201 與圖片資料

#### Scenario: 商品不存在

- **WHEN** 管理員對不存在的商品登錄圖片
- **THEN** 系統回傳 404

### Requirement: 依包裝類型維護相片組

系統 SHALL 以 `two_pack` 與 `single` 兩個相片組分別列出、登錄與排序圖片；其他組別值回傳 422。列出相片組時只回傳該組圖片，依排序值排列。

#### Scenario: 列出相片組

- **WHEN** 管理員查詢 `two_pack` 相片組
- **THEN** 只回傳兩粒裝相片

#### Scenario: 無效的組別

- **WHEN** 組別不是 `two_pack` 或 `single`
- **THEN** 系統回傳 422

#### Scenario: 未分組圖片不列入相片組

- **WHEN** 管理員查詢相片組
- **THEN** 回應不含未指定組別的圖片

### Requirement: 圖片排序

系統 SHALL 依請求更新圖片排序值並回傳排序後的清單；不屬於該商品或該相片組、或不存在的圖片 MUST 被略過。

#### Scenario: 調整順序

- **WHEN** 管理員送出新的排序值
- **THEN** 回傳的清單依新順序排列

#### Scenario: 含其他相片組的圖片

- **WHEN** 排序請求含其他相片組的圖片
- **THEN** 該圖片的排序值不變

### Requirement: 刪除圖片

系統 SHALL 刪除圖片紀錄並回傳 204，雲端儲存已設定時一併刪除檔案；圖片不存在時回傳 404。

#### Scenario: 刪除成功

- **WHEN** 管理員刪除圖片
- **THEN** 系統回傳 204，圖片不再出現於清單

#### Scenario: 圖片不存在

- **WHEN** 管理員刪除不存在的圖片
- **THEN** 系統回傳 404

### Requirement: 後台相片管理介面

後台 SHALL 在商品底下分別顯示兩粒裝與箱裝相片組，支援多檔上傳與拖曳排序；上傳失敗時 SHALL 列出失敗的檔名且保留成功的圖片，排序儲存失敗時 SHALL 還原原順序並顯示錯誤。規格編輯畫面僅預覽所屬相片組。

#### Scenario: 部分檔案上傳失敗

- **WHEN** 多檔上傳中有檔案失敗
- **THEN** 成功的圖片加入相片組，並顯示失敗的檔名

#### Scenario: 排序儲存失敗

- **WHEN** 拖曳後儲存排序失敗
- **THEN** 畫面還原原順序並顯示錯誤
