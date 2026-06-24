# CI 與手動部署指引

> 本專案規模小、單人低頻發版,**只保留 CI(PR 自動測試),部署改為手動**。
> 原本的全自動 CD(GitHub Actions 自動 build image → migrate → deploy)已移除,
> 因為它要對齊 WIF、部署 SA、Artifact Registry 等多項雲端資源,維護成本不划算。

## A. CI(已啟用,無需任何雲端設定)

`.github/workflows/ci.yml` 在每個 PR 與 push 到 `master` 時自動執行:

- **backend**:起一個 postgres service,`uv run pytest`(mypy 為 non-blocking)
- **frontend**:`npm run build`

CI **完全不碰 GCP / Vercel**,不需要 service account、WIF 或任何 secret。
唯一建議的設定是 branch protection(見 D 節)。

## B. 手動部署(需要時才做)

前提:本機已安裝並登入 `gcloud`、`vercel`,且帳號對應正確專案。

```bash
PROJECT=miao-fruit-shop-499505
REGION=asia-east1
```

### 1. 後端(Cloud Run,GCP 自動 build)
```bash
gcloud run deploy miao-api --source backend \
  --region=$REGION --project=$PROJECT
```
> 用 `--source`,GCP 會自動 build image(走 `cloud-run-source-deploy` repo),
> 不需要自己維護 Artifact Registry repo。既有的 env / secret / Cloud SQL 掛載會保留。

### 2. 資料庫 migration(有 schema 變更時才跑)
```bash
gcloud run jobs execute miao-api-migrate \
  --region=$REGION --project=$PROJECT --wait
```
> ⚠️ 此 job 必須掛上 Cloud SQL 才連得到 DB(`DB_HOST` 是 `/cloudsql/...` socket)。
> 若曾遇到連線失敗,先補掛載(只需做一次):
> ```bash
> gcloud run jobs update miao-api-migrate \
>   --region=$REGION --project=$PROJECT \
>   --set-cloudsql-instances=miao-fruit-shop-499505:asia-east1:miao-fruit-shop-db
> ```

### 3. 前端(Vercel production)
```bash
cd frontend && vercel --prod
```

> 部署規範:正式環境只能從 `master` 部署,部署前先確認變更已合併進 `master`。

## C. runtime SA 權限(部署相關,僅供參考)

Cloud Run 服務 / Job 的執行身分是預設 compute SA
`957573986284-compute@developer.gserviceaccount.com`,它需要:

- `roles/cloudsql.client`(連 Cloud SQL)✅ 已有
- 對所用 secret 的 `roles/secretmanager.secretAccessor`
  (`db-password`、`jwt-secret-key`、`LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`)✅ 已有

新增 secret 時,記得補授權:
```bash
gcloud secrets add-iam-policy-binding <SECRET_NAME> \
  --project=miao-fruit-shop-499505 \
  --member="serviceAccount:957573986284-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## D. Branch protection(建議)

Repo → Settings → Branches → Add rule(`master`):
- Require status checks to pass:勾選 `CI / backend`、`CI / frontend`
- Require branches to be up to date before merging
