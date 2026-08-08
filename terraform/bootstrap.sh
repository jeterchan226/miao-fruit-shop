#!/usr/bin/env bash
#
# 建 Terraform remote state 用的 GCS bucket(只需跑一次,local state)。
#
# 用法:
#   cd terraform && PROJECT=<new-project-id> ./bootstrap.sh
#   cd terraform && PROJECT=<new-project-id> ./bootstrap.sh --yes   # 略過確認
set -euo pipefail

REGION="${REGION:-asia-east1}"
PROJECT="${PROJECT:-}"
AUTO_YES=0
[ "${1:-}" = "--yes" ] && AUTO_YES=1

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$1"; }
err()  { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v terraform >/dev/null || { err "找不到 terraform CLI"; exit 1; }
command -v gcloud >/dev/null || { err "找不到 gcloud CLI"; exit 1; }
[ -n "$PROJECT" ] || { err "請帶 PROJECT=<gcp-project-id>"; exit 1; }

bold "1/3 檢查 GCP 帳號 / project"
CURRENT_ACCOUNT="$(gcloud config get-value account 2>/dev/null)"
echo "  目前登入帳號:${CURRENT_ACCOUNT:-<未登入>}"
gcloud projects describe "$PROJECT" >/dev/null 2>&1 || {
  err "project '$PROJECT' 不存在或目前帳號沒權限存取(gcloud projects describe 失敗)"
  exit 1
}
ok "project '$PROJECT' 存在且可存取"

bold "2/3 即將建立"
echo "  state bucket: ${PROJECT}-tfstate(region: $REGION)"
echo "  APIs: cloudresourcemanager / serviceusage / storage / iam"
if [ "$AUTO_YES" -ne 1 ]; then
  read -r -p "確定要在 '$PROJECT' 建立這些資源嗎?(y/N) " reply
  [ "$reply" = "y" ] || [ "$reply" = "Y" ] || { echo "已取消"; exit 0; }
fi

bold "3/3 terraform init + apply(bootstrap/,local state)"
cd "$SCRIPT_DIR/bootstrap"
terraform init -input=false
terraform apply -input=false -auto-approve \
  -var="project_id=$PROJECT" -var="region=$REGION"

BUCKET="$(terraform output -raw tfstate_bucket)"
ok "state bucket 建立完成:$BUCKET"
echo
echo "下一步(在 terraform/ 根目錄):"
echo "  terraform init -backend-config=\"bucket=${BUCKET}\""
echo "  cp terraform.tfvars.example terraform.tfvars   # 填 project_id/gcs_bucket_name 等"
echo "  ./apply.sh"
