#!/usr/bin/env bash
#
# 部署後端到 Cloud Run（miao-api）。
#
# 設計重點：
#   gcloud run deploy --source . 打包的是「本機工作目錄的檔案」，與 git remote 無關。
#   因此本腳本在部署前會強制檢查：分支在 master、本機 master 與 origin/master 同步、
#   工作目錄乾淨——避免把過時或未提交的程式碼部署上線。
#
#   環境變數與 Secret（DATABASE_URL/JWT_SECRET/LINE_CHANNEL_SECRET/LINE_LIFF_ID…）
#   已在 Cloud Run 服務上設定，gcloud run deploy 預設會保留，本腳本不碰它們。
#
# 用法：
#   cd backend && ./deploy.sh            # 互動式（部署前會問 y/N）
#   cd backend && ./deploy.sh --yes      # 略過確認，直接部署
#
# 可用環境變數覆寫預設值：SERVICE / REGION / PROJECT
set -euo pipefail

SERVICE="${SERVICE:-miao-api}"
REGION="${REGION:-asia-east1}"
PROJECT="${PROJECT:-miao-fruit-shop-499505}"
DEPLOY_BRANCH="master"

AUTO_YES=0
[ "${1:-}" = "--yes" ] && AUTO_YES=1

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$1"; }
err()  { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"

# 前置檢查 -----------------------------------------------------------------
command -v gcloud >/dev/null || { err "找不到 gcloud CLI"; exit 1; }
[ -f "$SCRIPT_DIR/Dockerfile" ] || { err "$SCRIPT_DIR 沒有 Dockerfile"; exit 1; }

bold "1/4 檢查 git 狀態（避免部署過時程式）"

CURRENT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$DEPLOY_BRANCH" ]; then
  err "目前在 '$CURRENT_BRANCH'，只能從 '$DEPLOY_BRANCH' 部署。請先：git checkout $DEPLOY_BRANCH"
  exit 1
fi

if ! git -C "$REPO_ROOT" diff --quiet || ! git -C "$REPO_ROOT" diff --cached --quiet; then
  err "工作目錄有未提交的變更，請先提交或清乾淨（部署吃的是工作目錄的檔案）"
  exit 1
fi

git -C "$REPO_ROOT" fetch origin "$DEPLOY_BRANCH" --quiet
BEHIND="$(git -C "$REPO_ROOT" rev-list --count "$DEPLOY_BRANCH..origin/$DEPLOY_BRANCH")"
if [ "$BEHIND" -gt 0 ]; then
  err "本機 $DEPLOY_BRANCH 落後 origin/$DEPLOY_BRANCH $BEHIND 個 commit（會部署到過時程式）。"
  err "請先同步：git pull origin $DEPLOY_BRANCH"
  exit 1
fi
AHEAD="$(git -C "$REPO_ROOT" rev-list --count "origin/$DEPLOY_BRANCH..$DEPLOY_BRANCH")"
ok "已在 ${DEPLOY_BRANCH}、未落後 origin（領先 ${AHEAD}，HEAD $(git -C "$REPO_ROOT" rev-parse --short HEAD)），工作目錄乾淨"

# 確認 ---------------------------------------------------------------------
bold "2/4 即將部署"
echo "  服務：$SERVICE"
echo "  區域：$REGION"
echo "  專案：$PROJECT"
echo "  來源：${SCRIPT_DIR}（--source .）"
if [ "$AUTO_YES" -ne 1 ]; then
  read -r -p "確定要部署到正式環境嗎？(y/N) " reply
  [ "$reply" = "y" ] || [ "$reply" = "Y" ] || { echo "已取消"; exit 0; }
fi

# 部署 ---------------------------------------------------------------------
bold "3/4 gcloud run deploy（既有 env/secret 會保留）"
gcloud run deploy "$SERVICE" \
  --source "$SCRIPT_DIR" \
  --region "$REGION" \
  --project "$PROJECT" \
  --quiet
ok "部署完成"

# 驗證 ---------------------------------------------------------------------
bold "4/4 驗證端點"
URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format='value(status.url)')"
echo "  服務網址：$URL"

HEALTH_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$URL/health" || true)"
echo "  GET  /health            → $HEALTH_CODE （期望 200）"

HOOK_CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/api/line/webhook" || true)"
echo "  POST /api/line/webhook  → $HOOK_CODE （期望 400 = 路由存在且簽章驗證生效）"

if [ "$HEALTH_CODE" = "200" ] && [ "$HOOK_CODE" = "400" ]; then
  ok "驗證通過：新版已上線，LINE Console 按 Verify 應會成功"
  echo "  Webhook URL：$URL/api/line/webhook"
else
  err "驗證未如預期；若 /api/line/webhook 回 404，代表上線的仍是舊版。請檢查部署輸出。"
  exit 1
fi
