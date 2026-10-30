## 1. 金額基礎情境

- [ ] 1.1 在 `backend/tests/test_admin_orders_api.py` 新增「修改訂單品項時規格已調價且改包裝類型」測試：既有訂單品項保留下單價與快照層數，新增規格以現況計算，`expected_total` 以此組合通過；此為 characterization test，預期直接通過，失敗則停下回報

## 2. ADR 修訂

- [ ] 2.1 依 design.md D2 修改 `docs/adr/0004-order-price-fixed-at-submission.md` 的標題、本文與 Considered Options，檔名不變
- [ ] 2.2 依 design.md D2 修改 `docs/adr/0003-backend-is-source-of-truth-for-amounts.md` 的重新計算依據，其餘句子不動

## 3. 驗證

- [ ] 3.1 `uv run ruff check .`
- [ ] 3.2 `uv run mypy app`
- [ ] 3.3 `uv run pytest -q`
- [ ] 3.4 確認兩份 ADR 使用 GLOSSARY 用語，且無「以規格現況重新計算」這句殘留
- [ ] 3.5 `openspec validate record-pack-snapshot-in-adr --strict`
