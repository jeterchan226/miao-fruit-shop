## Context

`POST /api/orders` 目前每個請求各建一筆訂單。`place_order` 在同一交易內鎖規格列、扣庫存、寫訂單後 commit，`create_order` 再推 LINE。代客下單共用 `place_order`。

商店頁已有 `submitting` state 並停用按鈕，但 state 要到下一次 render 才生效，同一輪事件內的連按擋不住；此外它防不了逾時後重試與 WebView 重送，所以 #29 決策為方案 A + B：後端 key 去重，前端產生 key 並鎖送出。ticket 的決策已定案，本文件只處理細節。

CORS 的 `allow_headers` 為 `*`，新 header 不需改設定。

## Goals / Non-Goals

**Goals:**

- 同一次送單最多成立一張訂單，包含同時送達的請求。
- 重送得到與首次相同的 `order_no`，顧客能看到訂單已成立。
- 部署期間新舊前後端可並存。

**Non-Goals:**

- 不比對重送內容與原訂單是否相同，也不為此回 422：ticket 決策為「撞到時回傳原訂單」，內容改變時由前端換 key。
- 不做前端自動重試，重試由顧客按鈕觸發。
- 不跨頁面重新整理保留 key。
- 不清除舊 key，也不設有效期限。
- 代客下單不加 key（後台單一管理員操作，不在 #29 範圍）。
- 不處理 `order_no` 撞號的自動重試（#30）。
- LINE 推播失敗或請求在 commit 後中斷時不補發通知。

## Decisions

**D1. Header 選填，缺少時走現行流程。** 必填會讓快取中的舊版前端在後端先上線時全數 422，導致無法下單。

**D2. 欄位為 `orders.idempotency_key`，nullable 字串，唯一約束。** Postgres 的唯一約束允許多個 NULL，代客下單與舊訂單不受影響，不需回填。長度上限 128 由 route 的 Header 驗證（`min_length=1`、`max_length=128`），避免無界輸入進 DB；不強制 UUID 格式，後端只把它當不透明字串。

**D3. 重送回 201，與首次回應相同。** 用戶端不需區分兩者，route 維持薄層，service 也不必回傳「是否新建」。替代方案 200 語意較精確，但沒有消費者需要這個區別。

**D4. `create_order` 分三段：先查、再建、失敗後再查。**

```python
async def create_order(session, data, idempotency_key=None):
    if idempotency_key is not None:
        existing = await order_repo.get_by_idempotency_key(session, idempotency_key)
        if existing is not None:
            return _to_order_read(existing)
    try:
        order = await place_order(..., idempotency_key=idempotency_key)
    except (IntegrityError, AppError):
        if idempotency_key is None:
            raise
        await session.rollback()
        existing = await order_repo.get_by_idempotency_key(session, idempotency_key)
        if existing is None:
            raise
        return _to_order_read(existing)
    await line_service.send_order_created(order)
    return _to_order_read(order)
```

先查放在最前面，所以重送不會碰到價格、庫存檢查（「原訂單成立後條件改變」情境）。

失敗後再查處理並發。只接 `IntegrityError` 不夠：兩個請求都通過先查後，輸的請求在規格列鎖上等待，贏的 commit 後它讀到庫存已歸零，拋出的是 `InsufficientStockError` 而不是唯一約束錯誤；同理也可能是 `PriceChangedError`。因此兩類都接，rollback 後查到原訂單就回傳，查不到（`order_no` 撞號，或真的業務失敗）就重新拋出，行為與現狀相同。替代方案 advisory lock 能完全序列化同 key 請求，但多一套鎖機制，且唯一約束仍要留作保險，否決。

`except` 中的 `raise` 須重新拋出原例外，實作時注意 `await` 不會清掉它。LINE 通知只在 `place_order` 成功路徑，重送與並發輸家都不會發。

**D5. `place_order` 新增 `idempotency_key: str | None = None`。** 代客下單不傳，呼叫端不變。key 不進 `OrderRead` 與 `AdminOrderRead`。

**D6. 前端 key 綁訂單內容。** 新增 pure module `checkoutKey.js`，提供 `nextCheckoutKey(previous, payload)`：`previous` 為 `{ key, fingerprint }` 或 null，fingerprint 為 `JSON.stringify(payload)`，相同時沿用，不同時產生新 key。`Cart.jsx` 以 ref 保存結果，訂單成立後清空。業務錯誤（409、404、422）後也不必主動換 key：失敗的請求不佔用 key，而顧客修改內容後 fingerprint 自然改變。

綁內容而非「每次進結帳頁」的原因：逾時後顧客回上一步改數量再送，若沿用舊 key 而舊請求其實成功，會靜默拿到內容不符的舊訂單。

**D7. UUID 產生要相容 iPadOS 15。** `crypto.randomUUID` 需 Safari 15.4 以上且僅限 secure context，目標裝置底線是 iPadOS 15。實作以 `randomUUID` 為主，缺少時用 `crypto.getRandomValues` 組 v4 UUID。

**D8. 按鈕鎖加 ref。** `next` 的 pay 步驟改以 `useRef` 同步判斷與設定，`submitting` state 繼續負責畫面。請求結束時（成功或失敗）解鎖。

**D9. `createOrder(payload, idempotencyKey)`。** 只在 `api.js` 加 `Idempotency-Key` header；`request` 已支援自訂 headers。

**D10. Migration 基於實作當下的 head。** 目前 dev 的 head 是 `b7e2d4f8a9c1`，但 PR #78（#46）新增的 `d3a91c7e5f20` 也接在它之後。實作時以 `alembic heads` 為準，不要寫死；若 #78 在本 ticket 開 PR 之後才合併，後合併者須改 `down_revision`，確保 `alembic heads` 只有一個 head。

## Testing Decisions

Seam 由高到低，皆沿用既有入口：

- **HTTP API**（`tests/test_orders_api.py`，prior art：`test_create_order_notifies_line_once`、`test_create_order_price_changed_409`）：相同 key 重送、庫存只扣一次、LINE 只發一次、條件改變後回原訂單、失敗不佔 key、不同 key、未帶 key、422 格式、回應不含 key。這是主要驗收入口。
- **Service against real commits**（新檔，比照 `tests/test_admin_order_concurrency.py` 用兩個 committing session 與 `asyncio.gather`）：相同 key 同時送達、同時搶最後庫存。`db_session` fixture 是單一連線，無法模擬並發，必須走此 seam；這也是 D4 失敗後再查路徑唯一的覆蓋。
- **DB constraint**（`tests/test_order_models.py`）：相同 key 第二筆寫入被拒、多筆 NULL 可共存。
- **Pure function**（新檔 `frontend/src/checkoutKey.test.js`，prior art：`pricing.test.js`）：`nextCheckoutKey` 沿用與換 key、UUID fallback 在無 `randomUUID` 時產生合法 v4。
- **API client**（`frontend/src/api.test.js`，以 `vi.stubGlobal` 模擬 `window` 與 `fetch`）：`createOrder` 帶 header。
- **手動**：前端無 jsdom 與 component 測試基礎，不為此新增依賴。「連續快速點擊」與「送出中再次點擊」在瀏覽器驗證，並確認發出一個請求。Migration 同樣手動：`upgrade head`、`downgrade -1`、`upgrade head`；`tests/conftest.py` 以 `create_all` 建表，不經 Alembic。

## Risks / Trade-offs

- [重送內容與原訂單不同時回傳原訂單] → 前端以 fingerprint 換 key；只有繞過前端的呼叫才會遇到，接受。
- [逾時後顧客改內容再送，舊請求其實已成功] → 會成立兩張訂單。這是顧客有意改內容，且比靜默回舊訂單安全；管理員可取消其中一張。
- [`line_friendship_status` 在 payload 內，逾時後從加好友頁返回會讓 fingerprint 改變而換 key] → 僅在逾時且中途改變好友狀態時發生，可能多一張訂單，接受；不為此把欄位排除在 fingerprint 外。
- [key 知情者可讀回訂單回應] → key 為隨機 UUID，公開回應本就不含顧客個資。
- [舊版前端快取] → 未帶 key 維持現行行為，部署後仍無保護直到頁面更新。
- [#30 同改建單外層] → #30 的 retry 包在 `create_order` 內部或 `place_order` 外層時，須保留 D4 的再查；本 ticket 先合併。
- [與 #78 的 migration 分叉] → 見 D10。
