# frontend-toolchain Specification

## Purpose
前端的 Node 版本宣告，以及 CI 對前端的安裝、測試、build 驗證。
## Requirements
### Requirement: Node 版本單一宣告

前端的 Node 版本 SHALL 只在 repo 內宣告一處，且 MUST 是官方仍在支援期內的 LTS 版本。CI 與 Vercel build MUST 依這個宣告取得 Node 版本，不得另行指定。

#### Scenario: CI 使用宣告的 LTS 版本
- **WHEN** CI 前端 job 執行
- **THEN** 該 job 使用的 Node 主版本等於 repo 宣告的版本，且該版本為支援期內的 LTS

#### Scenario: Vercel build 與 CI 版本一致
- **WHEN** Vercel 建置前端
- **THEN** build 使用的 Node 主版本等於 repo 宣告的版本，與 Vercel 專案設定中的版本無關

### Requirement: CI 依 lockfile 驗證前端

CI 前端 job SHALL 依 lockfile 安裝相依，再執行前端測試與 build；任一步驟失敗時 job MUST 失敗。

#### Scenario: 安裝、測試與 build 全數通過
- **WHEN** CI 前端 job 在 lockfile 與套件宣告一致的提交上執行
- **THEN** 相依安裝、前端測試與 build 皆成功，job 通過

#### Scenario: lockfile 不同步時失敗
- **WHEN** 提交的套件宣告與 lockfile 不一致
- **THEN** 相依安裝失敗，CI 前端 job 不通過

