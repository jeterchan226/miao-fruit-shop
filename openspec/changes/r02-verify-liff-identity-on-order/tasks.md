## 1. 紅燈：LINE ID token 驗證服務

- [ ] 1.1 新增 `tests/test_line_auth_service.py`：以模擬 HTTP 回應測試「有效 token 回傳 sub」「400 回應拋 `LineIdentityError`」「逾時拋 `LineVerifyUnavailable`」
- [ ] 1.2 執行測試確認失敗（模組不存在）

## 2. 綠燈：驗證服務

- [ ] 2.1 `core/config.py` 新增 `line_login_channel_id`、`line_id_token_required`、`order_rate_limit`
- [ ] 2.2 `core/exceptions.py` 新增 `LineIdentityError`（401 `LINE_IDENTITY_INVALID`）、`LineVerifyUnavailable`（503）
- [ ] 2.3 實作 `services/line_auth_service.verify_id_token()`，將 `httpx` 移到正式相依
- [ ] 2.4 執行 1.1 測試通過

## 3. 紅燈：下單流程套用身分驗證

- [ ] 3.1 在 `tests/test_orders_api.py` 新增：token 有效、`line_user_id` 與 sub 不符、token 無效、帶 userId 缺 token、無 LINE 身分，共 5 個情境
- [ ] 3.2 新增「身分驗證失敗時不扣庫存」斷言
- [ ] 3.3 確認測試失敗

## 4. 綠燈：下單流程

- [ ] 4.1 `schemas/order.py` 的 `CustomerCreate` 新增 `line_id_token: str | None`
- [ ] 4.2 `order_service.create_order` 在取鎖前呼叫驗證，並以 sub 覆寫 `line_user_id`
- [ ] 4.3 實作 `line_id_token_required=false` 的相容模式
- [ ] 4.4 執行 3.x 測試通過

## 5. 紅燈 → 綠燈：速率限制

- [ ] 5.1 在 `tests/test_orders_api.py` 新增「超過上限回 429」測試（測試中將上限設小），確認失敗
- [ ] 5.2 加入 `slowapi`，在 `main.py` 註冊 limiter 與 429 handler，`orders.create_order` 套用限制
- [ ] 5.3 確保其他測試不受限制影響（fixture 重設 limiter）

## 6. 前端

- [ ] 6.1 `line.js` 新增 `getLineIdToken()`
- [ ] 6.2 `Cart.jsx` 的 `buildOrderPayload` 帶上 `line_id_token`；`formatApiError` 處理 `LINE_IDENTITY_INVALID`、`RATE_LIMITED`
- [ ] 6.3 `npm run build`、`npm run test` 通過；LIFF 實機驗證下單

## 7. 重構與驗證

- [ ] 7.1 在 backend/ 執行 `uv run pytest -q` 全綠
- [ ] 7.2 `uv run ruff check .`、`uv run mypy app` 不新增錯誤

## 8. 收尾

- [ ] 8.1 Terraform 加入 `LINE_LOGIN_CHANNEL_ID=2007936913`、`LINE_ID_TOKEN_REQUIRED`、`ORDER_RATE_LIMIT`；CI workflow 補對應 Secrets
- [ ] 8.2 以 `feat(order): 以 LIFF ID token 驗證下單者 LINE 身分並加上速率限制` 提交
