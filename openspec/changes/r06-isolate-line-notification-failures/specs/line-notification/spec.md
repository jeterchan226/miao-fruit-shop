## ADDED Requirements

### Requirement: 推播失敗不影響下單結果
系統 SHALL 在訂單成功寫入資料庫後，於回應送出後才執行 LINE 推播；推播過程中任何例外 MUST 被捕捉並記錄，下單 API MUST 回應 201。

#### Scenario: Flex 建構發生非預期例外
- **WHEN** 建構 Flex 訊息時拋出 `ValueError`
- **THEN** 下單 API 回應 201，訂單存在於資料庫，且記錄一筆 warning log

#### Scenario: LINE API 逾時
- **WHEN** LINE push API 逾時
- **THEN** 下單 API 回應 201，回應時間不包含 LINE API 的等待時間

### Requirement: 替代文字符合 LINE 長度上限
系統 SHALL 將 Flex 訊息的 `alt_text` 限制在 1500 字元以內。

#### Scenario: 品項極多的訂單
- **WHEN** 訂單的純文字摘要超過 1500 字元
- **THEN** `alt_text` 被截斷為 1500 字元以內並以「…」結尾
