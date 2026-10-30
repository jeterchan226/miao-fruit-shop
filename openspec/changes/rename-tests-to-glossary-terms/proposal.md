Ticket: #86

## Why

GLOSSARY 把 `box` 列為箱裝的 _Avoid_，後端測試卻仍以 `box`、`pair`、`single` 命名規格與測試資料，同一個概念在測試裡有多種稱呼（PR #78 review 第 3 項）。讀測試的人要先翻譯才知道指的是哪種包裝類型，新測試也會照抄舊用語。

## What Changes

- 後端測試的函式名稱、區域變數與測試資料名稱統一命名：兩粒裝用 `two_pack`，箱裝用 `non_two_pack`。
- 包裝類型與該測試無關時，規格變數改用中性的 `spec`，不帶包裝類型。
- 不改任何正式程式碼、API 欄位與路徑、斷言與測試驗證的行為。

## User Stories

1. 身為後端開發者，我想要測試用的包裝類型稱呼只有一組，以便讀測試時不必先翻譯用語。
2. 身為後端開發者，我想要測試命名與正式程式碼的 `is_two_pack` 對得上，以便在兩邊搜尋同一個詞。
3. 身為後端開發者，我想要與包裝類型無關的測試不提包裝類型，以便一眼看出測試的重點。

## Capabilities

### New Capabilities
- `backend-test-naming`: 後端測試中包裝類型的命名方式

### Modified Capabilities

（無，產品行為不變。）

## Impact

- 僅 `backend/tests/`：`test_admin_create_order_api.py`、`test_admin_orders_api.py`、`test_order_items.py`、`test_order_service.py`、`test_admin_images_api.py`、`test_image_repo.py`、`test_image_service.py`、`test_product_service.py`。
- 正式程式碼、API、資料庫結構、依賴皆不變。
