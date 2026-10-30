## ADDED Requirements

### Requirement: 訂單詳情的訂單品項區塊標題

後台訂單詳情 SHALL 在檢視與編輯模式都以「訂單品項」作為區塊標題，MUST NOT 使用「商品明細」。

#### Scenario: 檢視模式

- **WHEN** 管理員開啟訂單詳情
- **THEN** 訂單品項區塊標題顯示「訂單品項」

#### Scenario: 編輯模式

- **WHEN** 管理員進入訂單編輯
- **THEN** 訂單品項區塊標題顯示「訂單品項」
