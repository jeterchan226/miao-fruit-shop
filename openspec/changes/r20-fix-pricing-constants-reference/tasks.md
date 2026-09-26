## 1. 紅燈

- [ ] 1.1 新增 `shared/pricing-cases.json`（至少：空購物車、單箱、滿額免運、2 粒裝奇偶、超過 3 層）
- [ ] 1.2 新增 `backend/tests/test_pricing_parity.py`：常數比對與案例比對
- [ ] 1.3 `frontend/src/pricing.test.js` 讀取共用案例並斷言
- [ ] 1.4 暫時修改 `pricing.js` 的 `FREE_SHIPPING` 確認 1.2 會失敗，再還原

## 2. 綠燈

- [ ] 2.1 修正 `constants.py` 註解為 `frontend/src/pricing.js`
- [ ] 2.2 若案例揭露差異，修正對應實作
- [ ] 2.3 執行 `uv run pytest tests/test_pricing_parity.py -q` 與 `npm run test` 皆通過

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`
- [ ] 3.2 CI 新增 `npm run test` 步驟（目前 frontend job 只有 build）

## 4. 收尾

- [ ] 4.1 以 `test(pricing): 新增前後端運費規則一致性測試並修正過期註解` 提交
