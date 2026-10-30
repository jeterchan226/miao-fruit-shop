## 1. 回應的訂單來源宣告為 enum

- [ ] 1.1 新增失敗測試：`GET /openapi.json` 的 `AdminOrderListItem`、`AdminOrderRead` 的 `source` 為 enum，值等於 `OrderSource`
- [ ] 1.2 `AdminOrderListItem.source`、`AdminOrderRead.source` 改為 `OrderSource`，測試轉綠
- [ ] 1.3 確認 `Order.source` 與資料庫結構未變，沒有新 migration

## 2. 驗證

- [ ] 2.1 `uv run ruff check .`
- [ ] 2.2 `uv run mypy app`
- [ ] 2.3 `uv run pytest -q`
- [ ] 2.4 在 PR 註明部署前置作業：對正式 DB 執行 `SELECT source, count(*) FROM orders GROUP BY source`，只有 `storefront`、`admin` 才可部署
