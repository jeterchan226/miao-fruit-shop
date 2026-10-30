## 1. 基準

- [ ] 1.1 確認 #57 未同時進行；執行 `pytest`，記下通過數
- [ ] 1.2 紅燈：`git grep -niE 'box|pair' -- backend/tests` 有命中；`git grep -ni single -- backend/tests` 有 API 路徑以外的命中

## 2. 訂單品項測試

- [ ] 2.1 `test_order_items.py`：依 design 對照改名；包裝類型無關的 `box` 改 `spec`，兩種包裝類型並存的測試用 `two_pack_spec`、`non_two_pack_spec`，並改測試函式名稱
- [ ] 2.2 `test_order_service.py`：改 `test_layers_*` 兩個測試名稱
- [ ] 2.3 執行這兩檔，確認通過

## 3. 後台訂單測試

- [ ] 3.1 `test_admin_orders_api.py`：改 `pair`、`box`、`pair_id`、`box_id` 與測試函式名稱
- [ ] 3.2 `test_admin_create_order_api.py`：改 `pair`
- [ ] 3.3 執行這兩檔，確認通過

## 4. 圖片測試

- [ ] 4.1 `test_image_repo.py`、`test_image_service.py`、`test_product_service.py`、`test_admin_images_api.py`：改 `single_imgs` 與 `single*.jpg` 測試資料，API 路徑不動
- [ ] 4.2 執行這四檔，確認通過

## 5. 驗證

- [ ] 5.1 綠燈：`git grep -niE 'box|pair' -- backend/tests` 無命中；`git grep -ni single -- backend/tests` 只剩 `images/group/single`
- [ ] 5.2 `git diff --stat` 只含 `backend/tests/`；`assert` 行的預期值未變
- [ ] 5.3 `ruff check .`、`mypy app`、`pytest` 通過，通過數與 1.1 相同
