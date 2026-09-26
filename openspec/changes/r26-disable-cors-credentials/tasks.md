## 1. 紅燈

- [ ] 1.1 `tests/test_cors.py`：預檢回應不含 `Access-Control-Allow-Credentials: true`
- [ ] 1.2 PATCH + `authorization,content-type` 預檢成功；PUT 預檢失敗
- [ ] 1.3 確認 1.1、1.2 的 PUT 情境失敗

## 2. 綠燈

- [ ] 2.1 `main.py` 設定 `allow_credentials=False`、`allow_methods`、`allow_headers`
- [ ] 2.2 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 grep `frontend/src` 的 `credentials:`，確認沒有 `include`
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`
- [ ] 3.3 部署後在 Vercel preview 與正式網址實測前台下單、後台登入與操作

## 4. 收尾

- [ ] 4.1 以 `fix(cors): 關閉 credentials 並收斂允許的方法與標頭` 提交
