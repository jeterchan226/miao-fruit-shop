## Context

前端 `line.js` 用 `liff.getProfile()` 取得 userId 後放進表單送出，後端完全不驗證。LIFF 提供 `liff.getIDToken()`，後端可呼叫 `POST https://api.line.me/oauth2/v2.1/verify`（form：`id_token`、`client_id`）驗證並取得 `sub`、`exp`、`aud`。

## Goals / Non-Goals

**Goals:**
- 讓 `line_user_id` 只能來自 LINE 簽發的 token。
- 降低匿名大量下單鎖庫存的風險。

**Non-Goals:**
- 不做 CAPTCHA、不要求非 LINE 環境登入。
- 不做跨 instance 的分散式速率限制（Cloud Run 多 instance 時每 instance 各自計數）。

## Decisions

- **呼叫 LINE verify API，而非本地驗 JWT**：LIFF ID token 以 ES256 簽章，本地驗需抓 JWKS 並處理輪替；verify API 簡單、官方推薦。代價是多一次外部呼叫（約 100ms），可接受。
- **以 `sub` 覆蓋請求中的 `line_user_id`**，並在兩者不符時拒絕，而非靜默覆蓋，方便偵測竄改。
- **速率限制用 `slowapi`（in-memory）**：替代方案 Cloud Armor 或 Redis 成本較高。以 `X-Forwarded-For` 第一個位址作為鍵（Cloud Run 在 GFE 後方）。
- 驗證邏輯放 `services/line_auth_service.py`，對外呼叫以 `httpx.AsyncClient`，測試中用 `respx` 或 monkeypatch 模擬。

## Risks / Trade-offs

- [LINE verify API 故障導致無法下單] → 逾時 3 秒；失敗時回 503 `LINE_VERIFY_UNAVAILABLE`，前端提示稍後再試。
- [前端尚未更新時後端先上線會擋掉所有 LINE 訂單] → 部署順序：先部署後端且設 `LINE_ID_TOKEN_REQUIRED=false`（缺 token 時把 `line_user_id` 當 null、不推播），前端上線後再改成 true。
- [多 instance 下速率限制可被分散繞過] → 目前流量極小，max instances 低，可接受。

## Migration Plan

1. Terraform 加 `LINE_LOGIN_CHANNEL_ID=2007936913`、`LINE_ID_TOKEN_REQUIRED=false` → 部署後端。
2. 部署前端（送出 `line_id_token`）。
3. 將 `LINE_ID_TOKEN_REQUIRED` 改為 true 重新部署。

## Resolved Questions

- LIFF 所屬 LINE Login channel ID：`2007936913`（2026-09-26 確認）。此值非機密，以一般環境變數 `LINE_LOGIN_CHANNEL_ID` 設定於 Cloud Run（Terraform 管理）。若測試 OA 使用不同的 LIFF／Login channel，測試環境需另設對應值。
