## 1. 紅燈

- [ ] 1.1 新增 `tests/test_openapi.py`：`POST /api/orders` 有 404、409，409 schema 含金額欄位
- [ ] 1.2 同檔新增：後台訂單狀態端點宣告 401、404、409 並引用 `ErrorResponse`
- [ ] 1.3 確認測試失敗

## 2. 綠燈

- [ ] 2.1 新增 `schemas/error.py` 的 `ErrorResponse`；調整 `PriceChangedResponse`
- [ ] 2.2 新增 `api/responses.py`，定義 `ORDER_CREATE_ERRORS`、`ADMIN_ERRORS`
- [ ] 2.3 `orders.py` 與後台 routes 套用 `responses=`
- [ ] 2.4 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 開啟 `/docs` 手動檢視錯誤回應描述
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `docs(api): 於 OpenAPI 宣告錯誤回應並啟用 PriceChangedResponse` 提交
