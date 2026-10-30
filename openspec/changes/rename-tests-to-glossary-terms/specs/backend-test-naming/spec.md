## ADDED Requirements

### Requirement: 箱裝的測試命名
後端測試 MUST 以 `non_two_pack` 稱呼箱裝，SHALL NOT 以 `box` 或 `single` 命名測試函式、區域變數或測試資料。API 路徑中的 `single` 是介面的一部分，不受此限。

#### Scenario: 測試不再使用 box
- **WHEN** 在後端測試中不分大小寫搜尋 `box`
- **THEN** 沒有任何命中

#### Scenario: single 只留在 API 路徑
- **WHEN** 在後端測試中不分大小寫搜尋 `single`
- **THEN** 每筆命中都是圖片群組 API 路徑的一部分

### Requirement: 兩粒裝的測試命名
後端測試 MUST 以 `two_pack` 稱呼兩粒裝，SHALL NOT 以 `pair` 命名測試函式、區域變數或測試資料。

#### Scenario: 測試不再使用 pair
- **WHEN** 在後端測試中不分大小寫搜尋 `pair`
- **THEN** 沒有任何命中

#### Scenario: 同一測試同時用到兩種包裝類型
- **WHEN** 一個測試同時建立兩粒裝與箱裝規格
- **THEN** 兩個變數分別以 `two_pack` 與 `non_two_pack` 命名

### Requirement: 與包裝類型無關的測試命名
包裝類型不影響結果的測試 SHALL 以中性名稱稱呼規格，不帶包裝類型。

#### Scenario: 測試只用到預設包裝類型的規格
- **WHEN** 測試的結果與規格的包裝類型無關
- **THEN** 規格變數命名為 `spec`，不是 `non_two_pack` 開頭的名稱

### Requirement: 改名不改變行為
改名 MUST NOT 改變測試驗證的行為、正式程式碼或 API。

#### Scenario: 測試數量不變
- **WHEN** 改名完成後執行後端全部測試
- **THEN** 全數通過，且通過數與改名前相同

#### Scenario: 斷言的值不變
- **WHEN** 比對改名前後的斷言
- **THEN** 差異只有被改名的識別字與測試資料名稱，預期值不變

#### Scenario: 正式程式碼不變
- **WHEN** 檢視此變更的差異
- **THEN** 只有後端測試有改動，API 欄位 `is_two_pack` 與圖片群組路徑維持原樣
