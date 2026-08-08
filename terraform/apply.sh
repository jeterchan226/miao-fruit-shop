#!/usr/bin/env bash
#
# 套用主要 GCP resource(Cloud Run / Cloud SQL / GCS / Secret Manager / Artifact Registry / IAM)。
# 先跑過 bootstrap.sh 建好 state bucket、terraform.tfvars 填好才能用。
#
# 用法:
#   cd terraform && ./apply.sh              # init(視需要)+ fmt check + validate + plan,問過才 apply
#   cd terraform && ./apply.sh --yes        # 略過 apply 前確認(仍會先印 plan)
#   cd terraform && ./apply.sh --plan-only  # 只跑到 plan,不 apply
set -euo pipefail

AUTO_YES=0
PLAN_ONLY=0
for arg in "$@"; do
  [ "$arg" = "--yes" ] && AUTO_YES=1
  [ "$arg" = "--plan-only" ] && PLAN_ONLY=1
done

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$1"; }
err()  { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

command -v terraform >/dev/null || { err "找不到 terraform CLI"; exit 1; }
[ -f terraform.tfvars ] || { err "沒有 terraform.tfvars,先 cp terraform.tfvars.example terraform.tfvars 並填值"; exit 1; }

bold "1/5 terraform fmt(檢查格式,不自動改)"
terraform fmt -check -diff -recursive || {
  err "格式不對齊,跑 'terraform fmt -recursive' 修完再重試"
  exit 1
}
ok "格式 OK"

bold "2/5 terraform init(已 init 過會是 no-op)"
[ -d .terraform ] || {
  err "尚未 init,先跑過 bootstrap.sh 拿到 bucket 名稱,再:"
  err "  terraform init -backend-config=\"bucket=<project_id>-tfstate\""
  exit 1
}
terraform init -input=false

bold "3/5 terraform validate"
terraform validate
ok "設定檔語法 OK"

bold "4/5 terraform plan"
terraform plan -input=false -out=.tfplan
if [ "$PLAN_ONLY" -eq 1 ]; then
  ok "--plan-only,結束(plan 存於 .tfplan)"
  exit 0
fi

bold "5/5 terraform apply"
if [ "$AUTO_YES" -ne 1 ]; then
  read -r -p "上面 plan 確認沒問題,要 apply 到真正 GCP 資源嗎?(y/N) " reply
  [ "$reply" = "y" ] || [ "$reply" = "Y" ] || { echo "已取消(plan 仍存於 .tfplan)"; exit 0; }
fi
terraform apply -input=false .tfplan
rm -f .tfplan
ok "apply 完成,下一步請看上面 next_steps output"
