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
