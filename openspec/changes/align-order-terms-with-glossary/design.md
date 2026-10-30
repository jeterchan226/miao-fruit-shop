## Context

`GLOSSARY.md` 的「訂單品項」_Avoid_ 列出「明細」，「兩粒裝」_Avoid_ 列出「2 粒」。#45 點名兩處違反；全庫搜尋後，同一用語在同一類介面還有另外三處：新訂單橫幅的替代摘要、規格表單的兩個勾選框、購物車的 `EVEN_QTY_REQUIRED` 替代提示。

前端目前只有純函式的 vitest，沒有元件測試環境（無 Testing Library、無 jsdom）。

## Goals / Non-Goals

**Goals:**

- 管理員與顧客看得到的「商品明細」改為「訂單品項」，指包裝類型的「2 粒裝」改為「兩粒裝」。
- 雙數限制的後端錯誤訊息有測試鎖定。

**Non-Goals:**

- 規格名稱與商品資料：「2 粒精緻禮盒」是規格的名稱，不是包裝類型的稱呼，種子資料、測試資料中的規格名稱與行銷文案（「2 粒禮盒」）都不動。
- 「訂單明細」：指整張訂單的詳情（後台 modal、LINE Flex Message、結帳成功說明），不是單一訂單品項，#45 未列入，要改請另開 ticket 並先更新 GLOSSARY。
- 「交易明細」：銀行轉帳的用語，與訂單品項無關。
- 只出現在程式註解的用語、錯誤代碼、API 形狀。
- 為前端補元件測試環境。

## Decisions

- **範圍涵蓋同用語的所有使用者可見處**，不限 #45 點名的兩處：只改一半會留下同樣的不一致，而且都是同一詞的一行文字替換，風險低。
- **購物車替代提示只換用語**：改為「兩粒裝商品請以雙數（2、4、6…）箱購買。」，其餘字句不動，與 `SpecGroupTabs` 的「箱購買」說法維持一致。
- **橫幅替代摘要改為「訂單品項」**：與區塊標題同一詞，不另造新詞。
- **修改既有 requirement 或新增 requirement 視現況而定**：`order-items`、`storefront-checkout`、`admin-order-notifications` 已有涵蓋的 requirement，用 MODIFIED；`admin-orders`、`admin-catalog` 目前沒有畫面用語的 requirement，用 ADDED。

## Testing Decisions

- **後端錯誤訊息：service against the test DB**。沿用 `apply_items` 這條最高的既有 seam，擴充 `test_two_pack_odd_qty_raises_even_qty_required`，以 `pytest.raises(...) as exc` 斷言 `exc.value.detail` 完整等於「精緻禮盒 為兩粒裝，請以雙數（2、4、6…）購買」。該測試的規格名稱須由「2 粒裝」改為「精緻禮盒」，否則訊息本身就含舊用語，斷言看不出差異。Prior art：`backend/tests/test_order_items.py`。
- **HTTP 層不加測試**：`test_admin_create_order_api.py` 已涵蓋 409 與代碼，訊息只經 exception handler 原樣傳遞。
- **前端訊息透傳：純函式**。`orderEdit.test.js` 中模擬後端 `EVEN_QTY_REQUIRED` 訊息的測試資料改為新字串（#45 指定）。它只驗證透傳，不是用語的紅燈測試。Prior art：同檔既有的錯誤對應測試。
- **JSX 文字沒有自動化 seam**：區塊標題、橫幅摘要、勾選框與購物車替代提示都寫在元件內，不為四行文字引入元件測試環境。改以驗證 group 的 `grep` 確認舊字串已消失，並在 dev server 的後台實際看過畫面。

## Risks / Trade-offs

- `detail` 文字改變：前端只顯示不比對，風險僅限若有外部依賴字串；本專案沒有。
- 與 #46 同改訂單品項 module：同檔不同行的小衝突，後合併者解掉即可。
- JSX 文字沒有回歸測試：之後有人寫回舊用語不會被 CI 擋下，以 review 把關。
