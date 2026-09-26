## ADDED Requirements

### Requirement: 上傳物件副檔名由內容類型決定
系統 SHALL 依 `content_type` 決定上傳物件的副檔名，且 MUST NOT 使用使用者提供的 `filename` 副檔名。

#### Scenario: 檔名副檔名與內容類型不符
- **WHEN** 請求簽名 `filename="evil.html"`、`content_type="image/png"`
- **THEN** 物件名稱以 `.png` 結尾

#### Scenario: 各允許類型的對照
- **WHEN** `content_type` 分別為 `image/jpeg`、`image/png`、`image/webp`、`image/gif`
- **THEN** 副檔名分別為 `jpg`、`png`、`webp`、`gif`

#### Scenario: 不支援的類型
- **WHEN** `content_type="image/svg+xml"`
- **THEN** 回應 422
