## ADDED Requirements

### Requirement: 錯誤訊息以訂單上的名稱稱呼訂單品項

系統 SHALL 在 `EVEN_QTY_REQUIRED` 與 `INSUFFICIENT_STOCK` 的錯誤訊息中，以規格名稱快照稱呼既有訂單品項，MUST NOT 使用規格改名後的現況名稱；尚未成立的新增訂單品項 SHALL 使用規格現況名稱。

#### Scenario: 雙數限制訊息用快照名稱

- **WHEN** 既有兩粒裝訂單品項的快照名稱為「精緻禮盒」，其規格已改名為「豪華禮盒」，請求把數量改為奇數
- **THEN** 系統回傳 409 `EVEN_QTY_REQUIRED`，錯誤訊息含「精緻禮盒」，不含「豪華禮盒」

#### Scenario: 庫存不足訊息用快照名稱

- **WHEN** 既有訂單品項的快照名稱為「精緻禮盒」，其規格已改名為「豪華禮盒」，請求增加的數量超過規格庫存
- **THEN** 系統回傳 409 `INSUFFICIENT_STOCK`，錯誤訊息含「精緻禮盒」，不含「豪華禮盒」

#### Scenario: 新增的訂單品項用規格現況名稱

- **WHEN** 新增名為「豪華禮盒」的規格，請求數量違反雙數限制或超過庫存
- **THEN** 錯誤訊息含「豪華禮盒」
