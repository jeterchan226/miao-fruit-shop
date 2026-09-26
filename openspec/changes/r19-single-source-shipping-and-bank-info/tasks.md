## 1. 紅燈

- [ ] 1.1 `tests/test_line_service.py`：購買須知文字與目前字串完全相同（保護重構）
- [ ] 1.2 monkeypatch `SHIPPING_BY_LAYER[1]=120` 後購買須知顯示「一層 $120」
- [ ] 1.3 monkeypatch `StoreInfo` 後 Flex 訊息與 `_order_text` 皆使用新帳號與新付款天數
- [ ] 1.4 確認 1.2、1.3 失敗

## 2. 綠燈

- [ ] 2.1 `core/constants.py` 新增 `StoreInfo`
- [ ] 2.2 `line_service` 新增 `build_purchase_notice()`，`POSTBACK_REPLIES` 改在請求時產生
- [ ] 2.3 `_order_text`、`_payment_rows`、Flex footer 改讀 `StoreInfo`
- [ ] 2.4 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `refactor(line): 購買須知與匯款資訊改由共用常數產生` 提交
