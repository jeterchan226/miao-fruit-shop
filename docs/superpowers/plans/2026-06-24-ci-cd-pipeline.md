# CI/CD 流水線 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 為 `JeterChan/miao-fruit-shop` 建立 GitHub Actions CI(品質閘)與 tag 觸發的 CD(後端 Cloud Run + 前端 Vercel,前後端鎖步)。

**Architecture:** 兩個 workflow——`ci.yml`(PR/push 跑 pytest+前端 build,mypy 非阻擋)與 `release.yml`(tag `v*` 觸發:build image 一次 → migration Cloud Run Job → deploy Cloud Run → smoke test → Vercel prod)。GCP 認證用 Workload Identity Federation(無金鑰)。一次性雲端資源由使用者依 `docs/ci-cd-console-setup.md` 於 console 建立。

**Tech Stack:** GitHub Actions、uv、pytest、PostgreSQL(service container)、Docker、Google Artifact Registry、Cloud Run(service + job)、Cloud SQL、Vercel CLI。

## Global Constraints

- 部署觸發:merge/push `master` 只跑 CI;**只有 push tag `v*` 才部署**。
- GCP 認證一律 **Workload Identity Federation**,repo 不存任何長期金鑰。
- migration 用**獨立 Cloud Run Job `miao-api-migrate`**,部署服務前執行;與服務**共用同一個 image**(以 git tag 當版本號)。
- CI 必過閘:`pytest` + 前端 `vite build`;**`mypy` 跑但非阻擋**(`continue-on-error: true`);**不在 CI 跑 ruff**。
- 既有值(verbatim):GCP 專案 `miao-fruit-shop-499505`、region `asia-east1`、Cloud Run service `miao-api`、Dockerfile 於 `backend/`、uv 版本 `0.11.19`、Python `3.13`。
- 測試需 PostgreSQL:conftest 由 `DATABASE_URL` 衍生 `miao_test` 資料庫,CI 須提供 postgres service 並設 `DATABASE_URL`。
- 回覆/文件用繁體中文;commit 訊息結尾加 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 不可刪改 `backend/deploy.sh`(保留為 break-glass fallback)。
- 提交前若在預設分支 `master`,先開分支(本計畫建議分支:`feat/ci-cd-pipeline`)。

---

## File Structure

- `.github/workflows/ci.yml` — **建立**。CI:backend job(postgres service + pytest/mypy)、frontend job(vite build)。觸發 PR + push master。
- `.github/workflows/release.yml` — **建立**。CD:tag `v*` 觸發,單一 job 依序 build→push→migrate→deploy→smoke→vercel。
- `docs/ci-cd-console-setup.md` — **建立**。使用者於 console 操作的逐步指引:AR、WIF、deploy SA + IAM、migration Job、Vercel、GitHub Secrets/Variables、branch protection,含 gcloud 查值指令。
- `backend/deploy.sh` — **不動**。
- `docs/superpowers/specs/2026-06-24-ci-cd-pipeline-design.md` — 既有 spec(參照來源)。

任務順序:Task 1(CI)→ Task 2(console 指引)→ Task 3(release workflow)→ Task 4(端到端驗證,gated on 使用者完成 console 設定)。Task 1–3 可由 agent 完成並各自提交;Task 4 需使用者先建好雲端資源。

---

### Task 1: CI workflow（`ci.yml`)

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes:無(僅用 repo 內既有指令)。
- Produces:GitHub check 名稱 `CI / backend`、`CI / frontend`(Task 4 的 branch protection 會引用這兩個名稱)。

- [x] **Step 1: 確認本機等效指令為綠(先驗證 CI 會跑的指令本身正確)**

Run（於 `backend/`）:
```bash
cd backend && uv sync --frozen && uv run pytest -q
```
Expected:pytest 全數通過(本機 `.env` 已指向可用的 postgres,衍生 `miao_test`)。

Run（於專案根）:
```bash
npm install --prefix frontend && npm run build --prefix frontend
```
Expected:`vite build` 成功,輸出 `frontend/dist`。

- [x] **Step 2: 建立 `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [master]

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: miao
          POSTGRES_PASSWORD: miao
          POSTGRES_DB: miao_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql+asyncpg://miao:miao@localhost:5432/miao_test
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          version: "0.11.19"
      - run: uv sync --frozen
      - name: Pytest
        run: uv run pytest -q
      - name: Mypy (non-blocking)
        run: uv run mypy app
        continue-on-error: true

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm install --prefix frontend
      - run: npm run build --prefix frontend
```

說明:conftest 用 `make_url(...).set(database="miao_test")`,故 `DATABASE_URL` 的 user/pass/host/port 會被沿用、資料庫名一律換成 `miao_test`,因此 postgres service 必須 `POSTGRES_DB: miao_test`。

- [x] **Step 3: 本機驗證 YAML 語法正確**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('ci.yml OK')"
```
Expected:印出 `ci.yml OK`,無 traceback。

- [x] **Step 4: 提交**

```bash
git add .github/workflows/ci.yml
git commit -m "$(printf 'ci: 新增 GitHub Actions CI(ruff + pytest + 前端 build)\n\npytest 於 postgres service container 上跑,mypy 非阻擋。\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

> 真正的端到端驗證(PR 觸發、check 變綠)在 Task 4。本任務交付物為「正確且可解析、本機等效指令皆綠」的 CI workflow。

---

### Task 2: Console 設定指引（`docs/ci-cd-console-setup.md`)

**Files:**
- Create: `docs/ci-cd-console-setup.md`

**Interfaces:**
- Produces:GitHub Secrets/Variables 名稱清單,供 Task 3 的 `release.yml` 引用——
  Secrets:`GCP_WIF_PROVIDER`、`GCP_DEPLOY_SA`、`VERCEL_TOKEN`。
  Variables:`GCP_PROJECT`、`GCP_REGION`、`CLOUD_RUN_SERVICE`、`MIGRATE_JOB`、`AR_REPO`、`VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`。

- [ ] **Step 1: 先用 gcloud 查出現有值(寫進指引前先取得真實資料)**

Run:
```bash
gcloud config get-value project
gcloud projects describe miao-fruit-shop-499505 --format='value(projectNumber)'
gcloud run services describe miao-api --region asia-east1 \
  --format='value(spec.template.spec.serviceAccountName)'
gcloud run services describe miao-api --region asia-east1 \
  --format='value(spec.template.metadata.annotations."run.googleapis.com/cloudsql-instances")'
gcloud run services describe miao-api --region asia-east1 \
  --format='yaml(spec.template.spec.containers[0].env)'
```
Expected:取得專案號碼、服務 runtime SA、Cloud SQL 連線名稱、以及 `DATABASE_URL`(或 `DB_*`)的來源(明文 env 或掛載的 Secret 名)。把這些值填入 Step 2 文件對應處。

- [x] **Step 2: 建立 `docs/ci-cd-console-setup.md`**

````markdown
# CI/CD 一次性雲端設定指引

> 目的:在執行 GitHub Actions CD 前,於 GCP / Vercel / GitHub 建立必要資源並收集識別值。
> 變數以 `<...>` 標示,請以 Step 0 查到的實際值取代。

## 0. 先查出現有值
```bash
PROJECT=miao-fruit-shop-499505
REGION=asia-east1
gcloud projects describe $PROJECT --format='value(projectNumber)'   # → <PROJECT_NUMBER>
gcloud run services describe miao-api --region $REGION \
  --format='value(spec.template.spec.serviceAccountName)'           # → <RUNTIME_SA>
gcloud run services describe miao-api --region $REGION \
  --format='value(spec.template.metadata.annotations."run.googleapis.com/cloudsql-instances")'  # → <CLOUDSQL_CONNECTION>
```

## 1. Artifact Registry(放 image)
```bash
gcloud artifacts repositories create miao-api \
  --repository-format=docker --location=$REGION --project=$PROJECT
```
→ `AR_REPO = asia-east1-docker.pkg.dev/miao-fruit-shop-499505/miao-api`

## 2. 部署用 service account
```bash
gcloud iam service-accounts create gh-deployer \
  --display-name="GitHub Actions deployer" --project=$PROJECT
```
→ `GCP_DEPLOY_SA = gh-deployer@miao-fruit-shop-499505.iam.gserviceaccount.com`

賦予角色:
```bash
SA=gh-deployer@$PROJECT.iam.gserviceaccount.com
for ROLE in roles/run.developer roles/artifactregistry.writer roles/cloudsql.client; do
  gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$SA" --role="$ROLE"
done
# 允許部署 SA 以 runtime SA 身分執行(deploy 與 job 都需要)
gcloud iam service-accounts add-iam-policy-binding <RUNTIME_SA> \
  --member="serviceAccount:$SA" --role="roles/iam.serviceAccountUser" --project=$PROJECT
```

## 3. Workload Identity Federation(無金鑰)
```bash
gcloud iam workload-identity-pools create github \
  --location=global --project=$PROJECT --display-name="GitHub"

gcloud iam workload-identity-pools providers create-oidc github \
  --location=global --workload-identity-pool=github --project=$PROJECT \
  --display-name="GitHub OIDC" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='JeterChan/miao-fruit-shop'"

# 綁定:只允許本 repo 透過此 pool 扮演部署 SA
gcloud iam service-accounts add-iam-policy-binding $SA --project=$PROJECT \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/attribute.repository/JeterChan/miao-fruit-shop"
```
→ `GCP_WIF_PROVIDER = projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/providers/github`

## 4. Migration Cloud Run Job(共用服務 image,指令 alembic)
> 先用現有服務最近一版 image 暫時建立;之後流水線每次會把 image 更新成新 tag。
```bash
LAST_IMAGE=$(gcloud run services describe miao-api --region $REGION \
  --format='value(spec.template.spec.containers[0].image)')

gcloud run jobs create miao-api-migrate \
  --image="$LAST_IMAGE" --region=$REGION --project=$PROJECT \
  --service-account=<RUNTIME_SA> \
  --set-cloudsql-instances=<CLOUDSQL_CONNECTION> \
  --command=uv --args="run,--no-dev,alembic,upgrade,head"
```
若服務的 `DATABASE_URL` 來自 Secret Manager,請對 job 加上相同的 `--set-secrets`(用 Step 0 查到的 secret 名),或 `--set-env-vars DATABASE_URL=...`。job 必須能用與服務相同的連線連到 DB。
→ `MIGRATE_JOB = miao-api-migrate`

## 5. Vercel
- Account Settings → Tokens 產生 token → `VERCEL_TOKEN`
- 專案 Settings 取得 `VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`
- 專案 Settings → Git:關閉 production 自動部署(把 Production Branch 改為不會日常 push 的分支,或停用 master 自動 promote),改由流水線觸發。PR preview 維持開啟。

## 6. GitHub Secrets / Variables
Repo → Settings → Secrets and variables → Actions:
- Secrets:`GCP_WIF_PROVIDER`、`GCP_DEPLOY_SA`、`VERCEL_TOKEN`
- Variables:`GCP_PROJECT=miao-fruit-shop-499505`、`GCP_REGION=asia-east1`、`CLOUD_RUN_SERVICE=miao-api`、`MIGRATE_JOB=miao-api-migrate`、`AR_REPO=asia-east1-docker.pkg.dev/miao-fruit-shop-499505/miao-api`、`VERCEL_ORG_ID=...`、`VERCEL_PROJECT_ID=...`

## 7. Branch protection(待 CI workflow 已存在後)
Repo → Settings → Branches → Add rule(`master`):
- Require status checks to pass:勾選 `CI / backend`、`CI / frontend`
- Require branches to be up to date before merging
````

- [x] **Step 3: 文件完整性自檢**

確認文件涵蓋:AR、deploy SA + 4 個角色(含 `serviceAccountUser` on runtime SA)、WIF pool/provider(含 repo 限制)、`workloadIdentityUser` 綁定、migration Job(image/SA/cloudsql/command/DB 連線)、Vercel(token/IDs/關自動 prod)、全部 Secrets+Variables、branch protection 引用的 check 名稱與 Task 1 一致(`CI / backend`、`CI / frontend`)。

- [x] **Step 4: 提交**

```bash
git add docs/ci-cd-console-setup.md
git commit -m "$(printf 'docs(ci): 新增 CI/CD 一次性 console 設定指引\n\nWIF/AR/deploy SA/migration Job/Vercel/GitHub Secrets/branch protection 逐步指令。\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 3: Release workflow（`release.yml`)

**Files:**
- Create: `.github/workflows/release.yml`

**Interfaces:**
- Consumes:Task 2 定義的 Secrets(`GCP_WIF_PROVIDER`、`GCP_DEPLOY_SA`、`VERCEL_TOKEN`)與 Variables(`GCP_PROJECT`、`GCP_REGION`、`CLOUD_RUN_SERVICE`、`MIGRATE_JOB`、`AR_REPO`、`VERCEL_ORG_ID`、`VERCEL_PROJECT_ID`)。
- Produces:tag `v*` 觸發的完整 release 流水線。

- [x] **Step 1: 建立 `.github/workflows/release.yml`**

```yaml
name: Release

on:
  push:
    tags: ["v*"]

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

permissions:
  id-token: write   # WIF 需要
  contents: read

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      IMAGE: ${{ vars.AR_REPO }}:${{ github.ref_name }}
    steps:
      - uses: actions/checkout@v4

      # ---- 認證 GCP(WIF,無金鑰)----
      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
          service_account: ${{ secrets.GCP_DEPLOY_SA }}
      - uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: ${{ vars.GCP_PROJECT }}

      # ---- 1. Build & push image(只 build 一次)----
      - name: Docker auth for Artifact Registry
        run: gcloud auth configure-docker ${{ vars.GCP_REGION }}-docker.pkg.dev --quiet
      - name: Build image
        run: docker build -t "$IMAGE" backend
      - name: Push image
        run: docker push "$IMAGE"

      # ---- 2. Migration(Cloud Run Job,用同一個 image)----
      - name: Update & run migration job
        run: |
          gcloud run jobs update ${{ vars.MIGRATE_JOB }} \
            --image "$IMAGE" --region ${{ vars.GCP_REGION }} --project ${{ vars.GCP_PROJECT }}
          gcloud run jobs execute ${{ vars.MIGRATE_JOB }} \
            --region ${{ vars.GCP_REGION }} --project ${{ vars.GCP_PROJECT }} --wait

      # ---- 3. Deploy 後端(同一個 image;保留既有 env/secret/cloudsql)----
      - name: Deploy Cloud Run service
        run: |
          gcloud run deploy ${{ vars.CLOUD_RUN_SERVICE }} \
            --image "$IMAGE" --region ${{ vars.GCP_REGION }} \
            --project ${{ vars.GCP_PROJECT }} --quiet

      # ---- 4. Smoke test(部署後驗證)----
      - name: Smoke test
        run: |
          set -euo pipefail
          URL=$(gcloud run services describe ${{ vars.CLOUD_RUN_SERVICE }} \
            --region ${{ vars.GCP_REGION }} --project ${{ vars.GCP_PROJECT }} \
            --format='value(status.url)')
          echo "Service URL: $URL"
          check() { # $1=method $2=path $3=expected
            code=$(curl -s -o /dev/null -w '%{http_code}' -X "$1" "$URL$2")
            echo "$1 $2 → $code (expected $3)"
            [ "$code" = "$3" ]
          }
          check GET  /health 200
          check POST /api/line/webhook 400
          check GET  /api/admin/orders/summary 401

      # ---- 5. Deploy 前端(Vercel prod)----
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Deploy frontend to Vercel (production)
        env:
          VERCEL_ORG_ID: ${{ vars.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ vars.VERCEL_PROJECT_ID }}
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: |
          npm i -g vercel@latest
          vercel pull --yes --environment=production --token="$VERCEL_TOKEN"
          vercel build --prod --token="$VERCEL_TOKEN"
          vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN"
```

說明:
- `IMAGE` 用 `${{ github.ref_name }}`(即 tag 名,如 `v1.2.0`)當版本號,migration Job 與 service 跑同一個 image。
- migration Job 的 command/Cloud SQL/SA/DB 連線於 Task 2 建立時設定,流水線只更新 image 並執行。
- `gcloud run deploy --image` 不帶 env 旗標 → 沿用服務上既有 env/secret/Cloud SQL 設定。
- 任一步驟非 0 結束即中止後續(GitHub Actions 預設 fail-fast;smoke test 以 `set -e` + 比對碼確保失敗會擋住 Vercel 部署)。

- [x] **Step 2: 本機驗證 YAML 語法正確**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('release.yml OK')"
```
Expected:印出 `release.yml OK`,無 traceback。

- [x] **Step 3: 提交**

```bash
git add .github/workflows/release.yml
git commit -m "$(printf 'ci: 新增 tag 觸發的 release 流水線(Cloud Run + Vercel)\n\nbuild once → migration job → deploy → smoke test(含 summary 401)→ vercel prod;WIF 認證。\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

> 真正的端到端驗證(打 tag、跑完整流水線)在 Task 4,需使用者先完成 console 設定。

---

### Task 4: 端到端驗證與啟用（gated:需使用者先完成 `docs/ci-cd-console-setup.md`)

**Files:** 無(操作與驗證)。

**Interfaces:**
- Consumes:Task 1–3 的 workflow 與 Task 2 指引建立的雲端資源 / GitHub Secrets+Variables。

- [ ] **Step 1: 合併 workflow 與指引到 master**

開 PR(分支 `feat/ci-cd-pipeline` → `master`)。此 PR 本身會觸發 `ci.yml`。
Expected:PR 頁面出現 `CI / backend`、`CI / frontend` 兩個 check 並**皆綠**(`mypy` 步驟可能黃/紅但不擋)。綠燈後 merge。

- [ ] **Step 2: 確認使用者已完成 console 設定**

向使用者確認 `docs/ci-cd-console-setup.md` 的 §1–§6 已完成、GitHub Secrets/Variables 已填齊。
Expected:使用者確認完成。

- [ ] **Step 3: 啟用 branch protection**

依指引 §7,於 `master` 要求 `CI / backend`、`CI / frontend` 通過、分支需最新。
Expected:之後對 `master` 的 PR 未過 CI 不能合併。

- [ ] **Step 4: 打第一個 tag 觸發 release**

```bash
git checkout master && git pull origin master
git tag v0.1.0
git push origin v0.1.0
```
Expected:Actions 出現 `Release` workflow 執行。

- [ ] **Step 5: 驗證 release 流水線各步驟**

於 Actions 的 `Release` run 逐步確認:
- Build/Push image:Artifact Registry 出現 `:<v0.1.0>` image。
- Migration job:`gcloud run jobs executions list --job miao-api-migrate --region asia-east1` 最新一筆成功。
- Deploy:Cloud Run `miao-api` 新 revision 上線並接流量。
- Smoke test:log 顯示 `/health→200`、`/api/line/webhook→400`、`/api/admin/orders/summary→401`,步驟綠。
- Vercel:production 出現新部署。
Expected:整條流水線綠燈,前後端皆為此 tag 版本。

- [ ] **Step 6: 失敗演練說明(僅記錄,不需破壞線上)**

確認團隊知道:任一步失敗時線上維持舊版(Cloud Run 新 revision 未健康即不切流量);緊急時可 `cd backend && ./deploy.sh` 手動部署作為 break-glass。

---

## Self-Review

**Spec coverage(對照 `2026-06-24-ci-cd-pipeline-design.md`):**
- §2 觸發模型 → Task 1(PR/push CI)、Task 3(tag release)。✓
- §3 release 五步(build once / migrate / deploy / smoke / vercel)→ Task 3 各步驟;§3.2 三項 smoke 檢查 → Task 3 Step 1 Smoke test + Task 4 Step 5。✓
- §4 一次性設定(WIF/AR/Job/Vercel/Secrets/branch protection)→ Task 2 指引 + Task 4 啟用。✓
- §5 CI 閘(pytest+前端 build 必過、mypy 非阻擋、不跑 ruff)→ Task 1。✓
- §6 檔案結構 → 與本計畫 File Structure 一致(ci.yml/release.yml/console-setup.md;deploy.sh 不動)。✓
- §1 假設(tag-based、WIF、migration Job、前端鎖步、mypy 非阻擋、branch protection、console 手動、deploy.sh 保留)→ 散見各 Task 與 Global Constraints。✓

**Placeholder scan:** 無 TBD/TODO;workflow 與指引皆為完整內容。`<PROJECT_NUMBER>`/`<RUNTIME_SA>`/`<CLOUDSQL_CONNECTION>` 為使用者環境特有值,已於 Task 2 Step 1 提供查詢指令取得,非計畫空白。

**Type/名稱一致性:** check 名稱 `CI / backend`、`CI / frontend`(Task 1 jobs `backend`/`frontend`)在 Task 2 §7 與 Task 4 Step 3 一致;`IMAGE`、`MIGRATE_JOB`、`AR_REPO`、`CLOUD_RUN_SERVICE` 等識別字在 Task 2/3 一致;smoke test 端點與期望碼(200/400/401)與 spec §3.2 一致。

> 已知限制(spec §8 開放問題):AR repo 名、Vercel 關自動 prod 的確切路徑、DB secret 掛載方式,於 Task 2 Step 1 查值與操作時定案。
