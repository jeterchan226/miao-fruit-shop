## MODIFIED Requirements

### Requirement: 後台列表介面的篩選對應

後台 SHALL 依瀏覽器當前時區把選到的日期轉為 UTC 時間範圍（起日 00:00 含、迄日隔天 00:00 不含）；搜尋字以 `MM-` 開頭（不分大小寫）時以訂單編號查詢，否則以關鍵字查詢；訂單來源選項「顧客下單」對應 `storefront`、「代客下單」對應 `admin`，選「全部」時不帶訂單來源。

#### Scenario: 日期區間

- **WHEN** 管理員選擇起訖日期
- **THEN** 請求帶起日當地 00:00 的 `created_from` 與迄日隔天當地 00:00 的 `created_before`

#### Scenario: 搜尋訂單編號

- **WHEN** 搜尋字以 `MM-` 開頭
- **THEN** 請求以 `order_no` 查詢

#### Scenario: 搜尋其他文字

- **WHEN** 搜尋字不是 `MM-` 開頭
- **THEN** 請求以 `q` 查詢

#### Scenario: 依訂單來源選項篩選

- **WHEN** 管理員選擇訂單來源「代客下單」
- **THEN** 請求以 `source=admin` 查詢

## ADDED Requirements

### Requirement: 代客下單標籤

後台 SHALL 在訂單列表與訂單詳情以「代客下單」標籤標示訂單來源為 `admin` 的訂單；顧客下單不標示。

#### Scenario: 代客下單顯示標籤

- **WHEN** 訂單來源為 `admin`
- **THEN** 訂單列表與訂單詳情顯示「代客下單」標籤

#### Scenario: 顧客下單不顯示標籤

- **WHEN** 訂單來源為 `storefront`
- **THEN** 訂單列表與訂單詳情不顯示標籤
