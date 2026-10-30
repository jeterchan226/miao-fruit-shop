## Context

`Order(...)` 完整字面值出現在 `test_admin_order_service.py`、`test_admin_orders_api.py`、`test_order_repo.py`（3 處）、`test_admin_order_concurrency.py`、`test_line_service.py`、`test_order_items.py`；ticket 只列前四檔，後兩檔是同一種重複，一併處理，否則新增必填欄位仍要改多處。規格 seed 另有 `_seed_spec`（`test_order_service.py`、`test_orders_api.py`）、`_seed_two_pack_spec`、`_seed_specs` + `_spec`（`test_order_items.py`、`test_admin_create_order_api.py`）、`_make_product_and_spec`、`_make_order_with_spec`。

各檔預設值並不相同，且部分斷言依賴這些值：`test_order_repo.py` 斷言 `total == 2030`，`test_line_service.py` 斷言地址字串，`test_admin_order_service.py` 斷言 LINE 欄位。

`tests/` 是 package，已有 `from tests.conftest import ...` 的先例。

## Goals / Non-Goals

**Goals:**
- 訂單必填欄位的預設值只在一處。
- 訂單相關測試的規格 seed 只有一套。
- 既有斷言一字不改。

**Non-Goals:**
- 商品、規格本身的目錄測試（`test_product_service.py`、`test_products_api.py`、`test_product_repo.py`、`test_spec_repo.py`、`test_admin_products_api.py`）的字面值：它們驗證的正是這些欄位，寫明比較清楚。
- 僅建商品的圖片測試 seed（`_seed_product`、`_seed`）、`_make_admin` / `_seed_admin`、`_auth_header`。
- 下單 API 的 request body helper（`_payload`、`_body`）：那是 HTTP 輸入，不是資料列。
- `test_order_items.py` 內無欄位的 `Order()`：不寫入資料庫，沒有重複可言。
- 引入 factory_boy 等新依賴。
- 正式程式碼的任何變更。

## Decisions

**放在 `backend/tests/factories.py`，用一般函式，不放 `conftest.py`、不做 fixture。** 測試需要帶參數呼叫，且同一測試常呼叫多次；並行測試用自己的 session，函式接 session 參數即可，不綁 `db_session` fixture。`conftest.py` 維持只放 fixture。

**不引入 factory_boy。** 它的 async SQLAlchemy 支援需要額外樣板，這裡幾個函式就夠。

**`build_*` 與 `create_*` 分開。** `build_*` 只建物件、不碰 session；`create_*` 接 session，`add` + `flush`，絕不 `commit`。並行測試用 `build_*` 自行 `add` + `commit`。

介面（名稱可微調，職責不變）：

```python
def build_order(order_no: str = "MM-TEST01", **overrides: Any) -> Order: ...
def build_order_item(spec: ProductSpec, *, qty: int, unit_price: int | None = None, **overrides: Any) -> OrderItem: ...
def build_spec(label: str = "A", **overrides: Any) -> ProductSpec: ...
def build_product(slug: str = "kanro", **overrides: Any) -> Product: ...

async def create_specs(session: AsyncSession, *specs: ProductSpec, slug: str = "kanro") -> list[ProductSpec]: ...
async def create_spec(session: AsyncSession, *, slug: str = "kanro", **overrides: Any) -> ProductSpec: ...
async def create_order_with_items(
    session: AsyncSession, order_no: str, *lines: tuple[ProductSpec, int, int], **overrides: Any
) -> Order: ...  # line = (規格, 數量, 下單價)
```

**覆寫用 `**overrides` 直接傳給 model 建構子。** SQLAlchemy 對不存在的欄位會丟 `TypeError`，打錯字不會被吞掉。`create_order_with_items` 先由 lines 算 `subtotal` / `total`、`shipping_fee=0`，再套 overrides，覆寫優先。

**`build_order` 預設值取 `test_admin_orders_api.py` 那份**（王小明、台北市中正區重慶南路1號、`2026-10-01`、`transfer`、880，LINE 欄位留 model 預設）。它最中性，也是最多檔共有的值。

**各檔特有的值保留成一行薄包裝。** `test_admin_order_service.py`（LINE 欄位）、`test_order_repo.py`（金額 2030、`linepay`）、`test_line_service.py`（地址、日期、金額、訂單品項）保留本地 `_make_order`，內容只是呼叫 `build_order` 並帶入該檔的覆寫值，不再列完整欄位。這樣近百個呼叫點不用動，斷言也維持原值。LINE 欄位不移進預設值，也不改由單一測試覆寫：`line_user_id` 有無可能走不同通知路徑，不在重構時改變測試的路徑。

**`test_admin_order_concurrency.py` 只換建立物件，清除邏輯不動。** `seeded` 仍自行 `commit`，`_delete_seeded` 維持原樣；它的固定 `_SLUG`、`_ORDER_NO` 透過參數傳入。

**slug 不自動產生。** 同測試需要多個商品時由呼叫端傳不同 `slug`，與現況（`kanro2`、`kanro3`）一致；自動序號會讓測試資料隨執行順序變動。

## Testing Decisions

- **入口**：service 對測試 DB 這一層，沿用 `db_session` fixture。新增 `backend/tests/test_factories.py` 驗證 spec 的 scenario：預設訂單可 flush 寫入、覆寫生效、錯誤欄位丟 `TypeError`、規格有 id 且同商品、金額由 lines 算出、覆寫金額優先、factory 不 commit（另一條連線讀不到，用 `engine` 開第二條連線）。
- **行為不變的驗證**：既有測試本身就是回歸網。改檔前記下 `pytest` 通過數，改完後通過數須等於原數加上 `test_factories.py` 新增數；`git diff` 中 `assert` 行不得變動。
- **Prior art**：`test_admin_order_service.py` 的 `_make_order`、`_make_order_with_item`；並行測試的 fixture 模式見 `test_admin_order_concurrency.py`。

## Risks / Trade-offs

- [預設值換掉後，隱性依賴舊值的測試失敗] → 逐檔改、每檔改完跑該檔；差異用覆寫補回，不改斷言。
- [`**overrides: Any` 失去欄位型別檢查] → 測試目錄不在 mypy 範圍，錯字由 model 建構子的 `TypeError` 擋下。
- [與其他進行中 ticket 動到同一批測試檔而衝突] → 重構不動斷言與呼叫點，衝突範圍僅限 helper 定義；後合併者 rebase 時改用工廠。
