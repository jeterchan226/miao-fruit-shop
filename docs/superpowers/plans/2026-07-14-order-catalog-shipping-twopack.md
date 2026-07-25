# 訂購單三項規則（免運/運費分級/2粒裝雙數）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 讓網頁商店反映實體訂購單三規則：同住址滿 $3000 免運、運費依層數分級（1/2/3 層 = $130/$150/$180）、2 粒裝規格須以雙數購買。

**Architecture:** 新增規格布林 tag `is_two_pack` 從 DB → schema → service → 前端 API → UI 一路打通。運費改由「層數」計算：非 2 粒裝每箱 1 層、2 粒裝每 2 箱 1 層；運費前後端共用同一公式，後端為權威（`expected_total` 比對）。2 粒裝雙數在前端 UI 約束、後端下單防呆。

**Tech Stack:** Backend FastAPI + SQLAlchemy + Alembic + pytest；Frontend React + Vite + vitest。

## Global Constraints

- 金額一律整數 NT$。
- 前後端運費公式必須完全一致，否則 `expected_total` 對不上 → `PRICE_CHANGED` 擋單。
- 層數公式：`總層數 = 非2粒箱數 + (2粒箱數 ÷ 2)`。
- 運費：`subtotal >= 3000 ? 0 : {1:130, 2:150, 3:180}[min(層數, 3)]`；層數 ≤ 0 時運費 0。
- 超過 3 層不特別處理（達 4 層必已免運），`>3` fallback 用 $180。
- tag 命名：後端 `is_two_pack`、前端 `isTwoPack`。
- Migration `add_column` 帶 `server_default='0'` 保護既有列。
- 回覆與說明文字一律繁體中文。

---

### Task 1: DB model + migration — `is_two_pack` 欄位

**Files:**
- Modify: `backend/app/models/product_spec.py`
- Create: `backend/alembic/versions/<generated>_add_is_two_pack_to_product_specs.py`
- Modify: `backend/app/cli.py`（seed 標記 2 粒裝）
- Test: `backend/tests/test_seed_product_cli.py`

**Interfaces:**
- Produces: `ProductSpec.is_two_pack: bool`（預設 `False`），供後續所有 task 使用。

- [x] **Step 1: 加 model 欄位**

在 `backend/app/models/product_spec.py`，於 `is_active` 欄位後加：

```python
    is_two_pack: Mapped[bool] = mapped_column(default=False)
```

- [x] **Step 2: 產生 migration 檔**

Run: `cd backend && alembic heads`（記下目前 head 的 revision id）
Run: `cd backend && alembic revision -m "add is_two_pack to product_specs"`

- [x] **Step 3: 填 migration 內容**

把新產生的 migration 檔 `upgrade`/`downgrade` 改成（`down_revision` 用 Step 2 記下的 head）：

```python
import sqlalchemy as sa
from alembic import op

# revision 由 alembic 產生，勿改
down_revision = "<HEAD_FROM_STEP2>"

def upgrade() -> None:
    op.add_column(
        "product_specs",
        sa.Column("is_two_pack", sa.Boolean(), nullable=False, server_default="0"),
    )

def downgrade() -> None:
    op.drop_column("product_specs", "is_two_pack")
```

- [x] **Step 4: 跑 migration 驗證**

Run: `cd backend && alembic upgrade head`
Expected: 無錯誤，`product_specs` 多出 `is_two_pack` 欄位。

- [x] **Step 5: seed 標記 2 粒裝**

在 `backend/app/cli.py` 的 specs 清單，把 `label="2 粒精緻禮盒"` 那筆 `ProductSpec(...)` 加參數 `is_two_pack=True`。

- [x] **Step 6: 更新 seed 測試**

在 `backend/tests/test_seed_product_cli.py` 找到驗證 specs 的斷言區塊，補一條：確認 label 含「2 粒」的 spec 其 `is_two_pack is True`、其餘為 `False`。範例（依現有測試風格調整取得 spec 的方式）：

```python
two = next(s for s in product.specs if "2 粒" in s.label)
assert two.is_two_pack is True
assert all(not s.is_two_pack for s in product.specs if "2 粒" not in s.label)
```

- [x] **Step 7: 跑測試**

Run: `cd backend && pytest tests/test_seed_product_cli.py -v`
Expected: PASS

- [x] **Step 8: Commit**

```bash
git add backend/app/models/product_spec.py backend/alembic/versions/ backend/app/cli.py backend/tests/test_seed_product_cli.py
git commit -m "feat(spec): add is_two_pack column, migration, seed mark"
```

---

### Task 2: Schema + service — 對外曝露 `is_two_pack`

**Files:**
- Modify: `backend/app/schemas/product.py`
- Modify: `backend/app/services/product_service.py`
- Test: `backend/tests/test_products_api.py`

**Interfaces:**
- Consumes: `ProductSpec.is_two_pack`（Task 1）。
- Produces: 公開 API `GET /api/products` 每個 spec 帶 `is_two_pack: bool`；`SpecCreate`/`SpecUpdate` 接受 `is_two_pack`。

- [x] **Step 1: 寫失敗測試**

在 `backend/tests/test_products_api.py` 加測試（沿用檔案既有 fixture / client 寫法）：

```python
async def test_public_products_expose_is_two_pack(client, seeded_product):
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    specs = resp.json()[0]["specs"]
    assert all("is_two_pack" in s for s in specs)
    assert any(s["is_two_pack"] for s in specs)
```

- [x] **Step 2: 跑測試確認失敗**

Run: `cd backend && pytest tests/test_products_api.py::test_public_products_expose_is_two_pack -v`
Expected: FAIL（回傳缺 `is_two_pack` key）

- [x] **Step 3: schema 加欄位**

在 `backend/app/schemas/product.py`：
- `PublicSpecRead` 加 `is_two_pack: bool`
- `AdminSpecRead` 加 `is_two_pack: bool`
- `SpecCreate` 加 `is_two_pack: bool = False`
- `SpecUpdate` 加 `is_two_pack: bool | None = None`

- [x] **Step 4: service 帶欄位**

在 `backend/app/services/product_service.py`，`_to_public_spec` 與 `_to_admin_spec` 的回傳各加：

```python
        is_two_pack=s.is_two_pack,
```

- [x] **Step 5: 跑測試確認通過**

Run: `cd backend && pytest tests/test_products_api.py -v`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/app/schemas/product.py backend/app/services/product_service.py backend/tests/test_products_api.py
git commit -m "feat(spec): expose is_two_pack in public/admin schemas"
```

---

### Task 3: 後端運費層數計算

**Files:**
- Modify: `backend/app/core/constants.py`
- Modify: `backend/app/services/order_service.py`
- Test: `backend/tests/test_order_service.py`

**Interfaces:**
- Consumes: `ProductSpec.price` / `ProductSpec.is_two_pack`。
- Produces:
  - `compute_layers(items: list[tuple[int, int, bool]]) -> int`（item = `(unit_price, qty, is_two_pack)`）
  - `compute_shipping(subtotal: int, layers: int) -> int`
  - `compute_amounts(items: list[tuple[int, int, bool]]) -> Amounts`（**簽名改變**：原本吃 `subtotal: int`）

- [x] **Step 1: 寫失敗測試**

在 `backend/tests/test_order_service.py` 加（import 依檔案既有風格）：

```python
from app.services.order_service import compute_amounts, compute_layers, compute_shipping

def test_layers_non_two_pack_one_per_box():
    assert compute_layers([(700, 3, False)]) == 3

def test_layers_two_pack_two_boxes_one_layer():
    assert compute_layers([(600, 4, True)]) == 2

def test_layers_mixed():
    assert compute_layers([(700, 1, False), (600, 2, True)]) == 2

def test_shipping_by_layer():
    assert compute_shipping(1000, 1) == 130
    assert compute_shipping(1000, 2) == 150
    assert compute_shipping(1000, 3) == 180
    assert compute_shipping(1000, 4) == 180  # >3 fallback

def test_shipping_free_over_threshold():
    assert compute_shipping(3000, 3) == 0

def test_shipping_zero_layers():
    assert compute_shipping(0, 0) == 0

def test_compute_amounts_mixed():
    amt = compute_amounts([(700, 1, False), (600, 2, True)])  # subtotal 1900, layers 2
    assert amt.subtotal == 1900
    assert amt.shipping_fee == 150
    assert amt.total == 2050
```

- [x] **Step 2: 跑測試確認失敗**

Run: `cd backend && pytest tests/test_order_service.py -k "layer or shipping or compute_amounts" -v`
Expected: FAIL（`compute_layers`/`compute_shipping` 未定義、`compute_amounts` 簽名不符）

- [x] **Step 3: constants 改門檻 + 加分級表**

在 `backend/app/core/constants.py`：

```python
FREE_SHIPPING_THRESHOLD = 3000  # subtotal 達此值(含)以上免運
SHIPPING_BY_LAYER = {1: 130, 2: 150, 3: 180}
COD_FEE = 30
```

刪除 `SHIPPING_FEE = 150`（改由層數決定）。

- [x] **Step 4: order_service 改公式**

在 `backend/app/services/order_service.py`：

改 import：

```python
from app.core.constants import FREE_SHIPPING_THRESHOLD, SHIPPING_BY_LAYER
```

替換 `compute_amounts`，並新增兩個 helper：

```python
def compute_layers(items: list[tuple[int, int, bool]]) -> int:
    # item = (unit_price, qty, is_two_pack)；非2粒每箱1層，2粒每2箱1層。
    layers = 0
    for _price, qty, is_two_pack in items:
        layers += qty // 2 if is_two_pack else qty
    return layers


def compute_shipping(subtotal: int, layers: int) -> int:
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    if layers <= 0:
        return 0
    return SHIPPING_BY_LAYER[min(layers, 3)]


def compute_amounts(items: list[tuple[int, int, bool]]) -> Amounts:
    # item = (unit_price, qty, is_two_pack)。cod_fee 永遠 0（僅剩轉帳）。
    subtotal = sum(price * qty for price, qty, _ in items)
    layers = compute_layers(items)
    shipping_fee = compute_shipping(subtotal, layers)
    return Amounts(
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        cod_fee=0,
        total=subtotal + shipping_fee,
    )
```

- [x] **Step 5: 更新 create_order 呼叫端**

在 `create_order` 內，把：

```python
    # 2) 伺服器權威重算金額
    subtotal = sum(spec.price * qty for spec, qty in locked)
    amounts = compute_amounts(subtotal)
```

改成：

```python
    # 2) 伺服器權威重算金額
    amounts = compute_amounts(
        [(spec.price, qty, spec.is_two_pack) for spec, qty in locked]
    )
```

- [x] **Step 6: 跑測試確認通過**

Run: `cd backend && pytest tests/test_order_service.py -v`
Expected: PASS（若既有測試呼叫舊 `compute_amounts(subtotal)`，一併改成新簽名）

- [x] **Step 7: Commit**

```bash
git add backend/app/core/constants.py backend/app/services/order_service.py backend/tests/test_order_service.py
git commit -m "feat(order): layer-based shipping (130/150/180), free over 3000"
```

---

### Task 4: 後端 2 粒裝雙數防呆

**Files:**
- Modify: `backend/app/core/exceptions.py`
- Modify: `backend/app/services/order_service.py`
- Test: `backend/tests/test_order_service.py`

**Interfaces:**
- Consumes: `ProductSpec.is_two_pack`。
- Produces: `EvenQtyRequiredError(AppError)`，`code = "EVEN_QTY_REQUIRED"`，`status_code = 409`；`create_order` 對 2 粒裝奇數 qty 拋此例外。

- [x] **Step 1: 寫失敗測試**

在 `backend/tests/test_order_service.py` 加（沿用檔案既有建單測試的 fixture / payload 寫法；`seeded` 需含一個 `is_two_pack=True` 的 spec）：

```python
import pytest
from app.core.exceptions import EvenQtyRequiredError

async def test_two_pack_odd_qty_rejected(session, two_pack_spec):
    payload = make_order_create(items=[(two_pack_spec.id, 3)])
    with pytest.raises(EvenQtyRequiredError):
        await create_order(session, payload)

async def test_two_pack_even_qty_ok(session, two_pack_spec):
    payload = make_order_create(items=[(two_pack_spec.id, 4)])
    order = await create_order(session, payload)
    assert order.order_no
```

> 註：若檔案沒有 `make_order_create`/`two_pack_spec` helper，依現有測試建立 payload 與 spec 的方式改寫；重點是「2 粒裝奇數 → 例外」「雙數 → 成功」。expected_total 需帶正確運費（4 箱 2 粒 = 2 層）。

- [x] **Step 2: 跑測試確認失敗**

Run: `cd backend && pytest tests/test_order_service.py -k two_pack -v`
Expected: FAIL（`EvenQtyRequiredError` 未定義）

- [x] **Step 3: 定義例外**

在 `backend/app/core/exceptions.py` 加：

```python
class EvenQtyRequiredError(AppError):
    code = "EVEN_QTY_REQUIRED"
    status_code = 409
```

（通用 `AppError` handler 已回 `{detail, code}`，無需改 `api/errors.py`。）

- [x] **Step 4: create_order 加驗證**

在 `backend/app/services/order_service.py`，import 加 `EvenQtyRequiredError`。於鎖定 `locked` 之後、`compute_amounts` 之前插入：

```python
    # 1.5) 2 粒裝須以雙數購買
    for spec, qty in locked:
        if spec.is_two_pack and qty % 2 != 0:
            raise EvenQtyRequiredError(f"{spec.label} 為 2 粒裝，請以雙數（2、4、6…）購買")
```

- [x] **Step 5: 跑測試確認通過**

Run: `cd backend && pytest tests/test_order_service.py -v`
Expected: PASS

- [x] **Step 6: Commit**

```bash
git add backend/app/core/exceptions.py backend/app/services/order_service.py backend/tests/test_order_service.py
git commit -m "feat(order): reject odd qty for 2-pack specs (EVEN_QTY_REQUIRED)"
```

---

### Task 5: 前端共用運費模組 + api.js 映射

**Files:**
- Create: `frontend/src/pricing.js`
- Create: `frontend/src/pricing.test.js`
- Modify: `frontend/src/api.js`

**Interfaces:**
- Produces:
  - `FREE_SHIPPING = 3000`
  - `computeLayers(items: {isTwoPack, count}[]) -> number`
  - `computeShipping(subtotal: number, layers: number) -> number`
  - api.js spec map 多帶 `isTwoPack`

- [x] **Step 1: 寫失敗測試**

Create `frontend/src/pricing.test.js`：

```javascript
import { describe, it, expect } from 'vitest';
import { FREE_SHIPPING, computeLayers, computeShipping } from './pricing.js';

describe('computeLayers', () => {
  it('非2粒每箱1層', () => {
    expect(computeLayers([{ isTwoPack: false, count: 3 }])).toBe(3);
  });
  it('2粒每2箱1層', () => {
    expect(computeLayers([{ isTwoPack: true, count: 4 }])).toBe(2);
  });
  it('混合', () => {
    expect(computeLayers([{ isTwoPack: false, count: 1 }, { isTwoPack: true, count: 2 }])).toBe(2);
  });
});

describe('computeShipping', () => {
  it('分級', () => {
    expect(computeShipping(1000, 1)).toBe(130);
    expect(computeShipping(1000, 2)).toBe(150);
    expect(computeShipping(1000, 3)).toBe(180);
    expect(computeShipping(1000, 4)).toBe(180);
  });
  it('滿門檻免運', () => {
    expect(computeShipping(FREE_SHIPPING, 3)).toBe(0);
  });
  it('零層免運費', () => {
    expect(computeShipping(0, 0)).toBe(0);
  });
});
```

- [x] **Step 2: 跑測試確認失敗**

Run: `cd frontend && npx vitest run src/pricing.test.js`
Expected: FAIL（找不到 `./pricing.js`）

- [x] **Step 3: 實作 pricing.js**

Create `frontend/src/pricing.js`：

```javascript
/* 運費與層數計算 — 與後端 order_service 公式一致 */

export const FREE_SHIPPING = 3000;
export const SHIPPING_BY_LAYER = { 1: 130, 2: 150, 3: 180 };

// 非2粒每箱1層；2粒每2箱1層。
export function computeLayers(items) {
  return items.reduce(
    (n, it) => n + (it.isTwoPack ? Math.floor(it.count / 2) : it.count),
    0
  );
}

export function computeShipping(subtotal, layers) {
  if (subtotal >= FREE_SHIPPING) return 0;
  if (layers <= 0) return 0;
  return SHIPPING_BY_LAYER[Math.min(layers, 3)];
}
```

- [x] **Step 4: 跑測試確認通過**

Run: `cd frontend && npx vitest run src/pricing.test.js`
Expected: PASS

- [x] **Step 5: api.js 映射 isTwoPack**

在 `frontend/src/api.js` 的 spec map（`normalizeProduct` 內），加一行：

```javascript
    isTwoPack: Boolean(spec.is_two_pack),
```

- [x] **Step 6: Commit**

```bash
git add frontend/src/pricing.js frontend/src/pricing.test.js frontend/src/api.js
git commit -m "feat(front): shared pricing module + isTwoPack mapping"
```

---

### Task 6: SpecCard 雙數步進 + App 帶 isTwoPack

**Files:**
- Modify: `frontend/src/SpecCard.jsx`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Consumes: `spec.isTwoPack`（Task 5）。
- Produces: cart item 物件帶 `isTwoPack`（供 Task 7 購物車列步進與 Task 8 運費計算）。

- [x] **Step 1: SpecCard 依 isTwoPack 步進**

在 `frontend/src/SpecCard.jsx` `SpecCard` 內，`const disabled = ...` 附近加：

```javascript
  const step = spec.isTwoPack ? 2 : 1;
```

把 `const [qty, setQty] = useState(1);` 改成：

```javascript
  const [qty, setQty] = useState(step);
```

把 qty 加減按鈕改為以 `step` 遞增／遞減、最小為 `step`：

```javascript
                <button onClick={() => setQty(q => Math.max(step, q - step))} aria-label="減少數量">−</button>
                <span className="v">{qty}</span>
                <button onClick={() => setQty(q => q + step)} aria-label="增加數量">+</button>
```

加入購物車後 reset 改為 `setQty(step)`：

```javascript
            onClick={() => { onAdd(p, spec, qty); setQty(step); }}
```

- [x] **Step 2: SpecCard 顯示雙數提示**

在 `specs__panel` 內（`spec.note` 那個 `specs__row` 之後）加條件提示：

```javascript
          {spec.isTwoPack && (
            <div className="specs__row">
              <span className="k">購買單位</span>
              <span className="specs__note">請以雙數（2、4、6…）箱購買</span>
            </div>
          )}
```

- [x] **Step 3: App.addToCart 帶 isTwoPack**

在 `frontend/src/App.jsx` `addToCart` 的新 cart 物件（`return [...prev, {...}]`）加欄位：

```javascript
        price: spec.price, count, isTwoPack: Boolean(spec.isTwoPack)
```

- [x] **Step 4: 手動驗證（建置通過）**

Run: `cd frontend && npx vite build`
Expected: 建置成功、無 lint/語法錯誤。

- [x] **Step 5: Commit**

```bash
git add frontend/src/SpecCard.jsx frontend/src/App.jsx
git commit -m "feat(front): 2-pack even-step qty on SpecCard + cart item tag"
```

---

### Task 7: 購物車列雙數步進 + 運費顯示

**Files:**
- Modify: `frontend/src/Cart.jsx`

**Interfaces:**
- Consumes: `FREE_SHIPPING`, `computeLayers`, `computeShipping`（Task 5）；cart item `isTwoPack`（Task 6）。

- [x] **Step 1: 換掉寫死常數，改用共用模組**

在 `frontend/src/Cart.jsx` 頂部，移除：

```javascript
const FREE_SHIPPING = 5000;
const SHIPPING_FEE  = 150;
```

改為 import：

```javascript
import { FREE_SHIPPING, computeLayers, computeShipping } from './pricing.js';
```

- [x] **Step 2: 改運費計算**

把：

```javascript
  const subtotal = useMemo(() => items.reduce((s, i) => s + i.price * i.count, 0), [items]);
  const shipping = subtotal === 0 ? 0 : (subtotal >= FREE_SHIPPING ? 0 : SHIPPING_FEE);
  const total    = subtotal + shipping;
```

改成：

```javascript
  const subtotal = useMemo(() => items.reduce((s, i) => s + i.price * i.count, 0), [items]);
  const layers   = useMemo(() => computeLayers(items), [items]);
  const shipping = subtotal === 0 ? 0 : computeShipping(subtotal, layers);
  const total    = subtotal + shipping;
```

- [x] **Step 3: 購物車列雙數步進**

在 `CartItem` 元件，qty 加減改為依 item 步進（2 粒裝 ±2、最小 step）：

```javascript
const CartItem = ({ item, onQty, onRemove }) => {
  const step = item.isTwoPack ? 2 : 1;
  return (
  <div className="cart-item">
    <div className="cart-item__img" style={{backgroundImage:`url(${item.image})`}}></div>
    <div>
      <p className="cart-item__t">{item.name}</p>
      <p className="cart-item__s">{item.specLabel} · {item.qty}</p>
      <div className="cart-item__row">
        <div className="qty">
          <button onClick={() => onQty(item.lineId, item.count - step)} aria-label="減少">−</button>
          <span className="v">{item.count}</span>
          <button onClick={() => onQty(item.lineId, item.count + step)} aria-label="增加">+</button>
        </div>
        <button className="cart-item__rm" onClick={() => onRemove(item.lineId)}>移除</button>
      </div>
    </div>
    <span className="cart-item__price">NT$ {(item.price * item.count).toLocaleString()}</span>
  </div>
  );
};
```

（`App.setQty` 已處理 `count <= 0` 移除，2 粒裝 count=2 減 2 = 0 → 移除，符合預期。）

- [x] **Step 4: 加運費說明文字（購物車 footer）**

在 `frontend/src/Cart.jsx` `step === 'cart'` 的 `drawer__foot` 內、`drawer__totals` 之後加說明：

```javascript
            <p className="drawer__ship-note">
              運費：一層 $130 / 二層 $150 / 三層 $180・同住址滿 NT$ 3,000 免運
            </p>
```

- [x] **Step 5: 手動驗證（建置通過）**

Run: `cd frontend && npx vite build`
Expected: 建置成功。免運進度條（`subtotal < FREE_SHIPPING`）自動用新門檻 3000。

- [x] **Step 6: Commit**

```bash
git add frontend/src/Cart.jsx
git commit -m "feat(front): layer shipping + 2-pack step + shipping note in cart"
```

---

### Task 8: 前端錯誤訊息 + Notices/Rail 文字

**Files:**
- Modify: `frontend/src/Cart.jsx`
- Modify: `frontend/src/Sections.jsx`

**Interfaces:**
- Consumes: 後端 `EVEN_QTY_REQUIRED` code（Task 4）。

- [x] **Step 1: formatApiError 對應 EVEN_QTY_REQUIRED**

在 `frontend/src/Cart.jsx` `formatApiError` 內，`PRICE_CHANGED` 判斷之後加：

```javascript
    if (err?.code === 'EVEN_QTY_REQUIRED') {
      return err?.data?.detail || '2 粒裝商品請以雙數（2、4、6…）箱購買。';
    }
```

- [x] **Step 2: 更新 Notices 付款方式文字**

在 `frontend/src/Sections.jsx` `NOTICES` 陣列，把 `title: '付款方式'` 那筆 body 的「五千元以上免運」改為「同住址滿 NT$ 3,000 免運」。

- [x] **Step 3: 更新 Rail 運費文字**

在 `frontend/src/Sections.jsx` `Rail` 內，把：

```javascript
        <div><h4>運費</h4><p>滿 NT$ 5,000 免運，未滿 150 元</p></div>
```

改成：

```javascript
        <div><h4>運費</h4><p>一層 $130 / 二層 $150 / 三層 $180，同住址滿 NT$ 3,000 免運</p></div>
```

- [x] **Step 4: 手動驗證（建置通過）**

Run: `cd frontend && npx vite build`
Expected: 建置成功。

- [x] **Step 5: Commit**

```bash
git add frontend/src/Cart.jsx frontend/src/Sections.jsx
git commit -m "feat(front): EVEN_QTY_REQUIRED message + shipping/free-ship copy"
```

---

### Task 9: Admin 規格表單「2 粒裝」勾選框

**Files:**
- Modify: `frontend/src/AdminApp.jsx`

**Interfaces:**
- Consumes: `AdminSpecRead.is_two_pack`（Task 2）；`updateSpec` 接受 `is_two_pack`（Task 2 `SpecUpdate`）。

- [x] **Step 1: form state 加 is_two_pack**

在 `frontend/src/AdminApp.jsx` `SpecEditModal` 的 `useState` 初始值加：

```javascript
    is_two_pack: spec.is_two_pack,
```

- [x] **Step 2: 送出 payload 帶 is_two_pack**

在 `handleSave` 的 `updateSpec(token, spec.id, {...})` payload 加：

```javascript
        is_two_pack: form.is_two_pack,
```

- [x] **Step 3: 加勾選框 UI**

在規格資訊表單（`adm-spec-form` 內，`is_active` 相關欄位附近；若無則置於表單末端）加：

```javascript
              <label className="adm-field adm-field--checkbox">
                <input
                  type="checkbox"
                  checked={form.is_two_pack}
                  onChange={(e) => setField('is_two_pack', e.target.checked)}
                />
                <span className="adm-field__label">2 粒裝（須以雙數購買）</span>
              </label>
```

- [x] **Step 4: 手動驗證（建置通過）**

Run: `cd frontend && npx vite build`
Expected: 建置成功。

- [x] **Step 5: Commit**

```bash
git add frontend/src/AdminApp.jsx
git commit -m "feat(admin): 2-pack checkbox in spec edit form"
```

---

### Task 10: 全端回歸驗證

**Files:** 無（僅執行）

- [x] **Step 1: 後端全測**

Run: `cd backend && pytest -q`
Expected: 全 PASS。特別確認 `test_order_service.py`、`test_products_api.py`、`test_seed_product_cli.py`、`test_schemas_order.py`。

- [x] **Step 2: 前端全測**

Run: `cd frontend && npx vitest run`
Expected: 全 PASS（含 `pricing.test.js`、既有 `notifications.test.js`）。

- [x] **Step 3: 前端建置**

Run: `cd frontend && npx vite build`
Expected: 建置成功。

- [x] **Step 4: 標記計畫完成並提交**

回本計畫檔把已完成 task 的 checkbox 改為 `- [x]`，提交：

```bash
git add docs/superpowers/plans/2026-07-14-order-catalog-shipping-twopack.md
git commit -m "docs: mark order-catalog plan tasks done"
```

---

## Self-Review

- **Spec coverage：** A（tag+雙數）→ Task 1/2/4/6/7/9；B（運費自動算）→ Task 3/5/7；C（說明文字）→ Task 7/8。三項全覆蓋。
- **Placeholder scan：** 無 TBD／TODO；所有程式步驟含實碼。測試 helper 名稱（`make_order_create`/`two_pack_spec`）已註明「依現有測試風格調整」，因無法預先得知既有 fixture 名稱。
- **Type consistency：** `is_two_pack`（後端）／`isTwoPack`（前端）一致；`compute_amounts` 新簽名 `list[tuple[int,int,bool]]` 於 Task 3 定義並在 create_order 同步更新；`computeLayers`/`computeShipping` 前後端命名對應公式一致。
