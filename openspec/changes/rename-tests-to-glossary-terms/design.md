## Context

PR #78 的 review 第 3 項指出新測試用 `box`，與 GLOSSARY 箱裝的 _Avoid_ 不符；既有測試同樣如此。

全 `backend/tests/` 搜尋結果：

- `box`：`test_admin_orders_api.py`、`test_order_items.py`、`test_order_service.py`。其中 `test_order_items.py` 的 `box` 多半是標籤為 `"A"` 的一般規格，包裝類型與測試無關。`test_order_service.py` 的 `one_per_box`、`two_boxes` 指的是數量，不是包裝類型。
- `pair`：`test_admin_create_order_api.py`、`test_admin_orders_api.py`、`test_order_items.py`。
- `single`：圖片群組 API 路徑 `group/single`，以及 `test_admin_images_api.py`、`test_image_repo.py`、`test_image_service.py`、`test_product_service.py` 的變數與測試資料。
- `two_pack`：已是最多的命名，對應 `is_two_pack` 欄位、圖片群組值 `two_pack`。

正式程式碼的 `is_two_pack`、`ImageGroup = Literal["two_pack", "single"]` 不在範圍內。

## Goals / Non-Goals

**Goals:**

- 全 `backend/tests/` 對兩種包裝類型只用一組命名。
- 測試不再出現 `box`、`pair`；`single` 只留在 API 路徑。

**Non-Goals:**

- `backend/app/`、API 欄位 `is_two_pack`、圖片群組路徑與值（`two_pack`、`single`）。
- 修改 GLOSSARY。`two-pack` 仍列在 _Avoid_，理由見 Decisions。
- 規格名稱（`"2 粒裝"`、`"5 台斤家庭箱"`、`"2 粒禮盒"`）：是規格的名稱，不是包裝類型的稱呼，沿用 `align-order-terms-with-glossary` 的判斷。
- 註解中的用語、斷言的預期值。
- 訂單編號、slug 等含 `PACK`、`pack` 的測試資料，以及 `_make_pack_order`：`pack` 不是 _Avoid_ 用語。
- `docs/`、已歸檔 OpenSpec、PR 紀錄中引用的舊測試名稱：歷史紀錄不回寫。
- 前端測試：ticket 範圍只有 `backend/tests/`。

## Decisions

**兩粒裝用 `two_pack`。** ticket 交由實作時決定命名，驗收只要求全檔一致。`two_pack` 是正式程式碼對這個概念的識別字（`is_two_pack`、圖片群組值），測試用同一個詞才能跨層搜尋。GLOSSARY 的 _Avoid_ `two-pack` 視為針對文件與對話的英文稱呼；只要 `is_two_pack` 不改，識別字層就沒有更好的選擇。改用 `pair` 不在 _Avoid_ 內，但 ticket 已點名它不一致，也對不上 `is_two_pack`。

**箱裝用 `non_two_pack`。** GLOSSARY 定義箱裝為「兩粒裝以外的包裝類型」，`test_layers_non_two_pack_one_per_box` 已有此用法，不必新造 `carton` 這類詞。

**命名對照：**

| 舊 | 新 |
|---|---|
| `pair`、`pair_id` | `two_pack_spec`、`two_pack_id` |
| `box`、`box_id`（測試涉及包裝類型） | `non_two_pack_spec`、`non_two_pack_id` |
| `box`（包裝類型與測試無關） | `spec` |
| `single_imgs` | `non_two_pack_imgs` |
| `"single.jpg"`、`"single-a.jpg"`、`"single-b.jpg"` | `"non-two-pack.jpg"`、`"non-two-pack-a.jpg"`、`"non-two-pack-b.jpg"` |
| `test_box_snapshot_allows_odd_qty_after_spec_became_two_pack` | `test_non_two_pack_snapshot_allows_odd_qty_after_spec_became_two_pack` |
| `test_existing_two_pack_snapshot_rejects_odd_qty_after_spec_became_box` | `test_existing_two_pack_snapshot_rejects_odd_qty_after_spec_became_non_two_pack` |
| `test_layers_non_two_pack_one_per_box` | `test_layers_non_two_pack_one_layer_per_qty` |
| `test_layers_two_pack_two_boxes_one_layer` | `test_layers_two_pack_two_qty_one_layer` |

**`test_admin_orders_api.py` 的 `_make_pack_order` docstring 已用 GLOSSARY 用語，不動。** 回傳值的解構跟著變數改名。

**`single` 一併處理。** ticket 標題只提 `box`，但 GLOSSARY 箱裝的 _Avoid_ 也列 `single`，範圍又要求全 `backend/tests/` 同一組命名；只留下 `single_imgs` 會與新命名並存。

## Testing Decisions

- **入口**：既有 pytest 全部測試，沿用 `client`、`db_session` fixture，不新增測試。這是純改名，既有測試就是回歸網。
- **命名檢查（無測試碼，靜態搜尋）**：`git grep -niE 'box|pair' -- backend/tests` 無命中；`git grep -ni single -- backend/tests` 只剩 `images/group/single`。改名前先跑一次確認有命中，作為紅燈。
- **行為不變**：改名前記下 `pytest` 通過數，改完須相同。`git diff` 中 `assert` 行的預期值不得變動，變的只有識別字。
- **Prior art**：`add-shared-test-factories` 的「`assert` 行不得變動」驗證方式。

## Risks / Trade-offs

- [與 #57（測試 factory 集中）改同一批測試檔] → 不可同時進行；#57 的 change 會動 `_spec`、`_seed_specs`、`_seed_two_pack_spec`，先合併者為準，後者 rebase。
- [與 #45 改同一測試] → #45 會把 `test_two_pack_odd_qty_raises_even_qty_required` 的規格名稱改掉，同檔同區小衝突，後合併者解掉。
- [`two_pack` 字面上接近 GLOSSARY 的 _Avoid_] → 接受，理由見 Decisions；若之後要改，應連同 `is_two_pack` 一起開 ticket。
- [`non_two_pack_spec` 較長] → 接受，換取與 GLOSSARY 定義及 `is_two_pack` 對應。
- [漏改] → 靜態搜尋把關；之後新測試寫回舊用語不會被 CI 擋下，以 review 把關。
