# 妙媽媽果園 — CI/CD 流水線設計

- 日期:2026-06-24
- 狀態:待審核
- 範圍:GitHub Actions 之 CI（品質閘）與 CD（後端 Cloud Run + 前端 Vercel）

---

## 1. 目標與範圍

為 `JeterChan/miao-fruit-shop`（GitHub public、預設分支 `master`）建立完整 CI/CD：

- **CI**:每次 PR / push 自動跑品質檢查，未通過不得合併進 `master`。
- **CD**:以 **git tag（`v*`）** 觸發正式部署，後端（GCP Cloud Run）與前端（Vercel）**鎖步**一起上 production。
- 部署流程內建 **DB migration** 與**部署後煙霧測試（smoke test）**。

### 現況（出發點）
- 目前**沒有任何 CI/CD**（無 `.github/workflows`、無 Cloud Build trigger）。
- 後端:Cloud Run 服務 `miao-api`，目前**手動**執行 [backend/deploy.sh](../../../backend/deploy.sh)（`gcloud run deploy --source .`，要求在 `master`、與 `origin/master` 同步、工作目錄乾淨）。連 Cloud SQL。
- 前端:Vercel，目前 push `master` 自動上 production。
- 後端工具:`pytest`（async）、`ruff`（E,F,I,UP,B）、`mypy --strict`（已設定）。
- Alembic 已存在（`backend/alembic/`，含多個 versions）。

### 不在本次範圍（明確排除）
- 清除既有 10 個 mypy strict 錯誤（另開 PR 處理；本次 mypy 設為非阻擋）。
- 新增前端 lint / 單元測試框架（前端目前無 eslint/vitest，CI 僅做 `vite build`）。
- 金流、通知等產品功能。
- 多環境（staging）流水線——本次僅 production 一個正式環境，外加 PR preview。

### 前提假設（已與使用者確認）
1. 部署觸發採 **tag-based**:merge 進 `master` 只跑 CI；打 `v*` tag 才部署。
2. GCP 認證採 **Workload Identity Federation（WIF，無金鑰）**。
3. Migration 採**獨立 Cloud Run Job**，於部署服務前執行。
4. 前端 production 改為**僅在 tag 時**上線（關閉 Vercel 對 `master` 的自動 prod），與後端鎖步；PR preview 維持自動。
5. CI 必過閘 = `pytest` + 前端 `vite build`；**mypy 跑但非阻擋**(不在 CI 跑 ruff)。
6. 開啟 `master` **branch protection**，要求 CI 通過才能合併。
7. 一次性前置雲端設定（WIF / Artifact Registry / migration Job / Vercel）**由使用者於 console 手動操作**；本 spec 提供逐步 checklist，不寫自動化腳本。
8. 保留 `deploy.sh` 作為 **break-glass 手動 fallback**。

---

## 2. 觸發模型

| 觸發事件 | 執行內容 | 是否上 production |
|---|---|---|
| 開 PR / push 到 PR 分支 | CI:後端 `pytest`（+ `mypy` 非阻擋）；前端 `vite build`。Vercel 自動出 preview | ❌ |
| merge / push 到 `master` | 同上 CI（確保 `master` 綠） | ❌ 只跑 CI，不部署 |
| push tag `v*`（如 `v1.2.0`） | 完整 release 流水線（見 §3） | ✅ 前後端一起上 prod |

設計理由:版本明確、可追溯；merge 與「上線」解耦，避免「前端自動上、後端還沒上」的版本落差（前後端皆鎖在同一個 tag）。

---

## 3. Release 流水線（tag `v*` 觸發）

依序執行，**任一步失敗即中止**，後續步驟不執行。

```
1. Build image   用 backend/Dockerfile build 一次，tag = 該 git tag（如 v1.2.0），
                 推送到 Artifact Registry。
2. Migrate       用「同一個 image」更新並執行 migration Cloud Run Job
                 （miao-api-migrate，指令 alembic upgrade head）。
3. Deploy 後端    用「同一個 image」deploy 到 Cloud Run service（miao-api）。
4. Verify 後端    對線上服務做 smoke test（見 §3.2）。
5. Deploy 前端    GitHub Action 以 Vercel token 觸發 vercel --prod。
```

### 3.1 Build once, deploy same image（關鍵設計）
- migration Job 與 service 跑的是**位元組完全相同**的 image（以 git tag 當版本號），杜絕「migration 用 A 版、服務跑 B 版」的落差。
- 比現行 `deploy.sh` 的 `--source .`（每次重新 build）更可重現、更快（image 只 build 一次）。

### 3.2 Smoke test（部署後驗證）
對線上服務 URL 實際發出請求，全部符合預期才算成功：

| 檢查 | 期望 | 意義 |
|---|---|---|
| `GET /health` | 200 | 服務已啟動、能回應 |
| `POST /api/line/webhook` | 400 | 路由存在且 LINE 簽章驗證生效（404 = 仍是舊版） |
| `GET /api/admin/orders/summary`（不帶 token） | 401 | 新版路由確實上線 + 管理員權限生效（404 = 仍是舊版） |

失敗時:該步驟紅燈、release 視為未成功並通知。由於 Cloud Run 採「新 revision 健康才切流量」，驗證失敗時線上通常仍為舊的健康版本，不會把壞版本推給使用者（等同有 rollback 底）。

### 3.3 失敗與回滾
- 步驟 1–4 任一失敗:新版未切流量，線上維持舊版；修正後重新打 tag（或刪除 tag 後重打）。
- 步驟 5（前端）失敗:後端已上、前端未上 → 需手動重觸發 Vercel 部署或修正後重打 tag。此為已知取捨（前端為流水線最後一步，降低「前端先上」的風險）。
- 緊急情況:用 `deploy.sh` 手動部署後端作為 break-glass。

---

## 4. 認證與一次性前置設定（使用者於 console 操作）

> 本節為 checklist；實際逐步操作指引將在實作計畫（plan）階段細化。

### 4.1 GCP — Workload Identity Federation
1. 建立 Artifact Registry repository（Docker 格式，region `asia-east1`）放 image。
2. 建立部署用 service account（如 `gh-deployer@<project>.iam`）。
3. 建立 Workload Identity Pool + Provider（GitHub OIDC），**限制只允許 `JeterChan/miao-fruit-shop` repo**（以 `attribute-condition` 綁 repository）。
4. 將 pool 的 principal 綁到部署 SA（`roles/iam.workloadIdentityUser`）。
5. 部署 SA 授予最小必要角色:
   - `roles/run.developer`（deploy Cloud Run 服務與 Jobs）
   - `roles/artifactregistry.writer`（推 image）
   - `roles/cloudsql.client`（migration Job 連 DB；服務本身亦需要）
   - `roles/iam.serviceAccountUser`（`actAs` 服務執行身分）

### 4.2 GCP — Migration Cloud Run Job
- 建立 Cloud Run Job `miao-api-migrate`：
  - 掛與 `miao-api` **相同的 Cloud SQL 連線**與 `DATABASE_URL` secret。
  - 進入點/指令:`alembic upgrade head`（於 `backend/` 工作目錄）。
  - 流水線每次部署會先把 Job 的 image 更新為新 tag 再執行。

### 4.3 Vercel
- 關閉「push `master` 自動上 production」（將 production 部署改為僅由流水線觸發；PR preview 維持自動）。
- 產生 **Vercel token**，記下 `VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`。

### 4.4 GitHub Secrets / Variables
- **Secrets**:`GCP_WIF_PROVIDER`（provider 資源名）、`GCP_DEPLOY_SA`（部署 SA email）、`VERCEL_TOKEN`。
- **Variables（非機密）**:`GCP_PROJECT=miao-fruit-shop-499505`、`GCP_REGION=asia-east1`、`CLOUD_RUN_SERVICE=miao-api`、`MIGRATE_JOB=miao-api-migrate`、Artifact Registry 路徑、`VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`。
- **DB 密碼等機密維持只在 Cloud Run / Cloud Run Job 上，不進 GitHub。**

### 4.5 GitHub — Branch protection
- 對 `master` 開啟保護:要求 §5 的 CI 檢查通過才能合併；要求分支為最新。

---

## 5. CI 閘（品質檢查）

於 PR 與 push 觸發。所有「必過」項目綠燈才允許合併進 `master`。

| 檢查 | 指令（於對應目錄） | 是否阻擋合併 |
|---|---|---|
| 後端測試 | `pytest`（`backend/`） | ✅ 必過 |
| 前端建置 | `vite build`（`frontend/`） | ✅ 必過 |
| 後端型別 | `mypy app`（`backend/`） | ⚠️ 跑但**非阻擋**（顯示結果，不擋；目前 10 個既有錯誤待另開 PR 清乾淨後升級為必過） |

說明:`pytest` 經驗證為綠燈，設為必過；前端目前無 lint/test，僅 build。本專案不在 CI 跑 ruff。

---

## 6. 預計新增 / 變更的檔案

```
.github/workflows/ci.yml          # PR/push:後端 pytest (+ mypy 非阻擋)、前端 vite build
.github/workflows/release.yml     # tag v*:build → migrate(Job) → deploy(Run) → smoke test → vercel --prod
docs/superpowers/specs/2026-06-24-ci-cd-pipeline-design.md   # 本文件
docs/ci-cd-console-setup.md       # 一次性 console 前置設定逐步指引（WIF / AR / Job / Vercel / Secrets / branch protection）
```

- `backend/deploy.sh`:**保留不動**，作為 break-glass 手動 fallback。
- 視需要:`backend` migration 進入點（若 Job 需要明確 command wrapper）；於 plan 階段確認是否需新增。

---

## 7. 元件邊界與職責

- **`ci.yml`**:只負責「驗證程式品質」，無任何雲端權限、不部署。輸入=程式碼，輸出=綠/紅燈。
- **`release.yml`**:只在 tag 觸發，負責「把指定版本送上線」。透過 WIF 取得短效 GCP 憑證、用 Vercel token 觸發前端；不持有任何長期金鑰。
- **Migration Job**:封裝「schema 遷移」這一件事，與服務共用 Cloud SQL 連線設定，獨立於服務生命週期。
- **Smoke test**:封裝「新版是否真的健康上線」的外部驗證，與部署步驟分離、可單獨理解。
- **`deploy.sh`**:手動 fallback，與自動流水線互不依賴。

---

## 8. 開放問題 / 待 plan 階段確認

1. Artifact Registry repository 命名與完整路徑（待使用者於 console 建立後回填）。
2. migration Cloud Run Job 的精確建立指令與 `DATABASE_URL` secret 掛載方式（與現行服務一致）。
3. Vercel 關閉自動 prod 的確切設定路徑（Production Branch 設定 vs Ignored Build Step），於 plan 階段確認。
4. 是否在 `release.yml` 失敗時加自動通知（e.g. GitHub 內建即可，暫不外接）。
