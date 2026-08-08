#!/usr/bin/env bash
#
# 灌 LINE Messaging API 憑證進 Secret Manager(terraform 只建空容器,值從
# LINE Developers Console 複製,不進 tfvars/state)。
#
# 用法:
#   cd terraform && PROJECT=<project-id> ./fill-line-secrets.sh
set -euo pipefail

PROJECT="${PROJECT:-}"
bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '\033[32m✓ %s\033[0m\n' "$1"; }
err()  { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; }

command -v gcloud >/dev/null || { err "找不到 gcloud CLI"; exit 1; }
[ -n "$PROJECT" ] || { err "請帶 PROJECT=<gcp-project-id>"; exit 1; }

bold "LINE Developers Console -> Messaging API channel -> Basic settings / Messaging API 分頁複製"

read -r -s -p "Channel access token: " TOKEN; echo
[ -n "$TOKEN" ] || { err "空值,取消"; exit 1; }
printf '%s' "$TOKEN" | gcloud secrets versions add line-channel-access-token \
  --project="$PROJECT" --data-file=-
ok "line-channel-access-token 已更新"

read -r -s -p "Channel secret: " SECRET; echo
[ -n "$SECRET" ] || { err "空值,取消"; exit 1; }
printf '%s' "$SECRET" | gcloud secrets versions add line-channel-secret \
  --project="$PROJECT" --data-file=-
ok "line-channel-secret 已更新"

echo
echo "注意:access token 與 channel secret 必須同一個 Messaging API channel(同一 provider),"
echo "否則 LIFF userId 推播不出去(見 project memory: LINE OA 拓樸)。"
