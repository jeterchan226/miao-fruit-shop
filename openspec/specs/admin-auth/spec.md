# admin-auth Specification

## Purpose

描述管理員的身分驗證：以帳號密碼登入取得 token、token 的有效條件、查詢目前管理員、以管理指令建立帳號，以及後台介面保存與清除登入狀態的方式。

## Requirements

### Requirement: 管理員登入

系統 SHALL 以表單格式的帳號密碼驗證管理員，成功時回傳 bearer access token；帳號不存在、密碼錯誤或帳號已停用時 MUST 回傳相同的 401 訊息「帳號或密碼錯誤」。

#### Scenario: 登入成功

- **WHEN** 管理員送出正確的帳號密碼
- **THEN** 系統回傳 `access_token` 與 `token_type` 為 `bearer`

#### Scenario: 密碼錯誤

- **WHEN** 密碼錯誤
- **THEN** 系統回傳 401 `AUTH_ERROR`

#### Scenario: 帳號已停用

- **WHEN** 已停用的管理員以正確密碼登入
- **THEN** 系統回傳 401 `AUTH_ERROR`

### Requirement: Token 驗證

系統 MUST 只接受簽章有效、未過期，且對應到存在並啟用中管理員的 token，否則回傳 401；token 有效期預設 480 分鐘。

#### Scenario: 無效 token

- **WHEN** 請求帶格式錯誤或簽章不符的 token
- **THEN** 系統回傳 401

#### Scenario: 過期 token

- **WHEN** 請求帶已過期的 token
- **THEN** 系統回傳 401

#### Scenario: 管理員已停用或不存在

- **WHEN** token 對應的管理員已停用或不存在
- **THEN** 系統回傳 401

### Requirement: 查詢目前管理員

系統 SHALL 以 token 回傳目前管理員的識別碼、帳號與啟用狀態，MUST NOT 回傳密碼雜湊。

#### Scenario: 帶有效 token

- **WHEN** 管理員以有效 token 查詢
- **THEN** 系統回傳管理員資料

#### Scenario: 未帶 token

- **WHEN** 未帶 token 查詢
- **THEN** 系統回傳 401

### Requirement: 建立管理員

系統 SHALL 提供管理指令建立管理員，以雜湊保存密碼；密碼少於 8 字元、帳號已存在或兩次輸入不一致時 MUST 中止。系統 MUST NOT 提供建立管理員的 HTTP API。

#### Scenario: 建立成功

- **WHEN** 以未使用的帳號與合法密碼執行指令
- **THEN** 建立啟用中的管理員，密碼以雜湊保存

#### Scenario: 密碼過短

- **WHEN** 密碼少於 8 字元
- **THEN** 指令中止

#### Scenario: 帳號已存在

- **WHEN** 帳號已存在
- **THEN** 指令中止

### Requirement: 後台登入狀態

後台 SHALL 把 token 保存在瀏覽器；開啟時以 token 查詢目前管理員，失敗時清除 token 並顯示登入畫面。任何後台查詢回傳 401 或管理員按登出時 SHALL 清除 token 回到登入畫面。

#### Scenario: 沒有 token

- **WHEN** 瀏覽器沒有保存的 token 就開啟後台
- **THEN** 顯示登入畫面

#### Scenario: 保存的 token 失效

- **WHEN** 開啟後台時保存的 token 已失效
- **THEN** 清除 token 並顯示登入畫面

#### Scenario: 登入失敗

- **WHEN** 登入回傳錯誤
- **THEN** 登入畫面顯示錯誤訊息

#### Scenario: 登出

- **WHEN** 管理員按登出
- **THEN** 清除 token 並回到登入畫面
