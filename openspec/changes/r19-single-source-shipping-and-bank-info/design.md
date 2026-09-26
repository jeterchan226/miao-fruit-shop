## Context

「請於 3 日內完成轉帳」同時出現在 `_order_text`、Flex footer、購買須知三處；運費說明只在購買須知。

## Goals / Non-Goals

**Goals:** 每項業務數值只有一個定義點。

**Non-Goals:** 不把店家資訊改成可由後台編輯（需要 DB 與 UI，另案）；不改訊息視覺設計。

## Decisions

- **放在 `core/constants.py`，而非 `Settings`（環境變數）**：銀行資訊不因環境而異，也不是機密；放進 Secret/env 反而增加部署步驟。
- `StoreInfo` 用 `@dataclass(frozen=True)` 單例，測試可用 monkeypatch 替換整個物件。
- `build_purchase_notice()` 依 `sorted(SHIPPING_BY_LAYER)` 產生「一層／二層／三層」，中文數字以小對照表轉換。
- `POSTBACK_REPLIES` 改為在請求時呼叫 builder，而非模組載入時固定字串，才能反映 monkeypatch 後的值。

## Risks / Trade-offs

- [重構時意外改動使用者看到的文字] → 先加「文字與現行完全相同」的快照測試再重構。
