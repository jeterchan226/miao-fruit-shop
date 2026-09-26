## Why

審查 #26：`CORSMiddleware` 設定 `allow_credentials=True`，但前後端認證都走 `Authorization: Bearer` header，沒有使用 cookie。開啟 credentials 沒有功能上的必要，卻讓任何被 CORS 白名單或 regex 放行的來源都能攜帶瀏覽器憑證；若日後 regex 被放寬或引入 cookie，會直接擴大攻擊面。

## What Changes

- `allow_credentials` 改為 `False`。
- `allow_methods` 從 `*` 收斂為實際使用的 `GET, POST, PATCH, DELETE`；`allow_headers` 收斂為 `Authorization, Content-Type`。
- 回應不再帶 `Access-Control-Allow-Credentials: true`。

## Capabilities

### New Capabilities
- `cors-policy`: 後端跨來源請求的允許範圍。

### Modified Capabilities
（無）

## Impact

- `backend/app/main.py`
- 測試：`tests/test_cors.py`
- 前端需確認 `fetch` 沒有使用 `credentials: 'include'`（若有需移除，否則請求會被瀏覽器擋下）
