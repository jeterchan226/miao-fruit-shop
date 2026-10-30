## MODIFIED Requirements

### Requirement: 兩粒裝須以雙數購買

系統 MUST 拒絕數量有變動且為奇數的兩粒裝訂單品項，回傳 409 `EVEN_QTY_REQUIRED`；錯誤訊息 MUST 以「兩粒裝」稱呼包裝類型，MUST NOT 使用「2 粒裝」。

#### Scenario: 奇數數量

- **WHEN** 請求以數量 3 購買兩粒裝規格
- **THEN** 系統回傳 409 `EVEN_QTY_REQUIRED`

#### Scenario: 雙數數量

- **WHEN** 請求以數量 4 購買兩粒裝規格
- **THEN** 訂單品項成立

#### Scenario: 錯誤訊息用語

- **WHEN** 請求以奇數數量購買名為「精緻禮盒」的兩粒裝規格
- **THEN** 錯誤訊息為「精緻禮盒 為兩粒裝，請以雙數（2、4、6…）購買」
