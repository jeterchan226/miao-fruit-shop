# 前台商品呈現改版：包裝群組 Tabs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把商店區塊從「每個 spec 一張獨立 SpecCard（各自輪播圖）」改成「箱裝／兩粒裝兩個 Tab，各自共用一組圖片輪播 + 緊湊規格列表」。

**Architecture:** 新增 `SpecGroupTabs.jsx` 取代 `SpecCard.jsx`，在前端把 `product.specs` 依既有 `spec.isTwoPack` 欄位分成兩組（不動後端、不動 `spec.images` 分組邏輯）。Tab 內沿用現有輪播邏輯（搬移自 `SpecCard.jsx`），規格清單從「一張卡一個規格」改成「一組內多列」，維持現有的多規格各自加入購物車互動。`App.jsx` 只需替換渲染呼叫，`Cart.jsx`/`pricing.js`/`addToCart` 資料形狀不變。

**Tech Stack:** React 18 + Vite（frontend），無新增依賴。

## Global Constraints

- 前台目標裝置基準 iPadOS 15 Safari/WebKit：CSS 漸層不可用 `transparent`，首載圖片維持輕量。
- 前端沒有元件層級單元測試慣例，UI 互動一律瀏覽器手動驗證，不為 UI 元件硬湊假測試。
- 商店架構鎖定「單一商品（甘露梨）+ 多規格」，本次只是同一商品內的呈現分組，不引入多商品目錄抽象。
- 正式部署只能從 `master` 分支；本次先在目前分支開發，完成後由使用者決定何時合併/部署（部署本身不在本計畫範圍）。

---

## Task 1: 建立 `SpecGroupTabs` 元件，取代 `SpecCard` 渲染

**Files:**
- Create: `frontend/src/SpecGroupTabs.jsx`
- Modify: `frontend/src/App.jsx:9`（import）、`frontend/src/App.jsx:144-150`（渲染呼叫）
- Delete: `frontend/src/SpecCard.jsx`（改版後無任何引用者）

**Interfaces:**
- Consumes：`product` 物件（形狀來自 `frontend/src/api.js` 的 `listProducts()`，含 `product.id`、`product.name`、`product.sub`、`product.slug`、`product.season`、`product.specs[]`，每個 spec 為 `{ id, label, qty, price, stock, stockText, note, isTwoPack, images }`）；`onAdd(product, spec, count)` callback（即 `App.jsx` 的 `addToCart`，签名不變）。
- Produces：`SpecGroupTabs({ product, onAdd })` 元件，`App.jsx` 直接渲染，不回傳任何新的共用型別給其他任務用。

### Step 1: 讀懂要搬移的舊邏輯（不用寫檔，只是確認起點）

`frontend/src/SpecCard.jsx` 目前結構（改版後會刪除這個檔案，邏輯拆到 `SpecGroupTabs.jsx` 裡）：
- 輪播狀態：`imgIdx`／`slidesRef`／`timerRef`，`scrollToSlide`／`goTo`／`resetTimer`／`handleDotClick`。
- Body：名稱／副標／`specs__panel`（內容、備註、庫存文字、兩粒裝購買單位提示）／`pcard__foot`（價格、qty stepper、加入購物車按鈕，`step = spec.isTwoPack ? 2 : 1`）。

### Step 2: 寫 `SpecGroupTabs.jsx`

Create `frontend/src/SpecGroupTabs.jsx`:

```jsx
/* Spec group tabs — 兩粒裝／箱裝兩組，各自共用一組圖片輪播 + 緊湊規格列表 */

import { useEffect, useRef, useState } from 'react';

const stockLabel = (s) => s === 'in' ? '現貨供應' : s === 'low' ? '剩量不多' : '已售完';

const GROUPS = [
  { key: 'box', label: '箱裝', filter: (s) => !s.isTwoPack },
  { key: 'twopack', label: '兩粒裝', filter: (s) => s.isTwoPack },
];

const Price = ({ value }) => (
  <span className="price">
    <span className="pre">NT$</span>{value.toLocaleString()}
  </span>
);

const GroupCarousel = ({ images, season }) => {
  const [imgIdx, setImgIdx] = useState(0);
  const slidesRef = useRef(null);
  const timerRef = useRef(null);

  const scrollToSlide = (i) => {
    const track = slidesRef.current;
    if (track) track.scrollTo({ left: track.clientWidth * i, behavior: 'smooth' });
  };

  const goTo = (i) => {
    setImgIdx(i);
    scrollToSlide(i);
  };

  const resetTimer = () => {
    clearInterval(timerRef.current);
    if (images.length <= 1) return;
    timerRef.current = setInterval(() => {
      setImgIdx((prev) => {
        const next = (prev + 1) % images.length;
        scrollToSlide(next);
        return next;
      });
    }, 3500);
  };

  useEffect(() => {
    resetTimer();
    return () => clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images.length]);

  const handleDotClick = (i) => {
    goTo(i);
    resetTimer();
  };

  return (
    <div className="pcard__carousel">
      <div className="pcard__slides" ref={slidesRef}>
        {images.length > 0 ? images.map((url, i) => (
          <div key={i} className="pcard__slide" style={{ backgroundImage: `url(${url})` }} />
        )) : (
          <div className="pcard__slide pcard__slide--empty" />
        )}
      </div>
      <span className="pcard__season">產季 {season}</span>
      {images.length > 1 && (
        <div className="pcard__dots">
          {images.map((_, i) => (
            <button
              key={i}
              className={'pcard__dot' + (i === imgIdx ? ' is-active' : '')}
              onClick={() => handleDotClick(i)}
              aria-label={`圖片 ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const SpecRow = ({ p, spec, onAdd }) => {
  const step = spec.isTwoPack ? 2 : 1;
  const [qty, setQty] = useState(step);
  const disabled = spec.stock === 'out';

  return (
    <div className="spec-row">
      <div className="spec-row__info">
        <h3 className="spec-row__name">{spec.label}</h3>
        <div className="specs__panel">
          <div className="specs__row">
            <span className="k">內容</span>
            <span>{spec.qty}</span>
          </div>
          {spec.note && (
            <div className="specs__row">
              <span className="k">備註</span>
              <span className="specs__note">{spec.note}</span>
            </div>
          )}
          <div className="specs__row">
            <span className="k">狀態</span>
            <span className={'stock stock--' + spec.stock}>{stockLabel(spec.stock)}</span>
          </div>
          {spec.isTwoPack && (
            <div className="specs__row">
              <span className="k">購買單位</span>
              <span className="specs__note">請以雙數（2、4、6…）箱購買</span>
            </div>
          )}
        </div>
      </div>
      <div className="spec-row__actions">
        <Price value={spec.price} />
        <div className="speccard__actions">
          {!disabled && (
            <div className="qty">
              <button onClick={() => setQty(q => Math.max(step, q - step))} aria-label="減少數量">−</button>
              <span className="v">{qty}</span>
              <button onClick={() => setQty(q => q + step)} aria-label="增加數量">+</button>
            </div>
          )}
          <button
            className="btn btn--primary"
            disabled={disabled}
            onClick={() => { onAdd(p, spec, qty); setQty(step); }}
          >
            {disabled ? '已售完' : '加入購物車'}
          </button>
        </div>
      </div>
    </div>
  );
};

export const SpecGroupTabs = ({ product: p, onAdd }) => {
  const groups = GROUPS.map(g => ({ ...g, specs: p.specs.filter(g.filter) }));
  const defaultGroup = groups.find(g => g.key === 'box' && g.specs.length > 0)
    ?? groups.find(g => g.specs.length > 0)
    ?? groups[0];
  const [activeKey, setActiveKey] = useState(defaultGroup.key);
  const active = groups.find(g => g.key === activeKey) ?? defaultGroup;
  const images = active.specs[0]?.images || [];
  const productSub = p.sub ? p.sub.split(' · ')[1] : p.slug;

  return (
    <article className="pcard spec-group">
      <GroupCarousel key={active.key} images={images} season={p.season} />
      <div className="pcard__body">
        <div className="pcard__head">
          <h2 className="pcard__name">{p.name}</h2>
          <p className="pcard__sub">{productSub || p.name}</p>
        </div>
        <div className="specs__tabs">
          {groups.map(g => {
            const empty = g.specs.length === 0;
            return (
              <button
                key={g.key}
                type="button"
                className={'specs__tab' + (g.key === active.key ? ' is-active' : '') + (empty ? ' specs__tab--empty' : '')}
                disabled={empty}
                onClick={() => setActiveKey(g.key)}
              >
                {g.label}
                {empty && <span className="num">無商品</span>}
              </button>
            );
          })}
        </div>
        <div className="spec-rows">
          {active.specs.map(spec => (
            <SpecRow key={spec.id} p={p} spec={spec} onAdd={onAdd} />
          ))}
        </div>
      </div>
    </article>
  );
};
```

### Step 3: 修改 `App.jsx` 的 import 與渲染

`frontend/src/App.jsx:9` 目前：

```jsx
import { SpecCard } from './SpecCard.jsx';
```

改成：

```jsx
import { SpecGroupTabs } from './SpecGroupTabs.jsx';
```

`frontend/src/App.jsx:144-150` 目前：

```jsx
            <div className="shop__grid shop__grid--specs">
              {products.flatMap(p =>
                p.specs.map(spec => (
                  <SpecCard key={p.id + '-' + spec.id} p={p} spec={spec} onAdd={addToCart} />
                ))
              )}
            </div>
```

改成：

```jsx
            <div className="shop__grid shop__grid--specs">
              {products.map(p => (
                <SpecGroupTabs key={p.id} product={p} onAdd={addToCart} />
              ))}
            </div>
```

### Step 4: 刪除 `SpecCard.jsx`

```bash
rm frontend/src/SpecCard.jsx
```

### Step 5: 確認沒有殘留引用

```bash
grep -rn "SpecCard" frontend/src
```

Expected: 沒有任何輸出（`SpecGroupTabs` 不會被這個字串匹配到）。

### Step 6: Commit

```bash
git add frontend/src/SpecGroupTabs.jsx frontend/src/App.jsx
git rm frontend/src/SpecCard.jsx
git commit -m "feat(front): replace per-spec SpecCard grid with package-group tabs"
```

---

## Task 2: 新增/調整 CSS — Tab 空狀態、緊湊規格列

**Files:**
- Modify: `frontend/assets/site.css`（在既有 `.specs__tabs`/`.specs__tab` 規則附近，約 448-465 行；在 `.specs__panel` 規則附近，約 466-478 行）

**Interfaces:**
- Consumes：Task 1 產出的 `SpecGroupTabs.jsx` 所使用的 class 名稱：`.spec-group`、`.specs__tab--empty`、`.spec-rows`、`.spec-row`、`.spec-row__info`、`.spec-row__name`、`.spec-row__actions`。
- Produces：無（純樣式，不被其他任務消費）。

`.specs__tabs`／`.specs__tab`／`.is-active`／`.specs__panel`／`.specs__row`／`.qty`／`.price`／`.stock`／`.pcard__carousel` 等既有 class 直接沿用，不用重新定義。

### Step 1: 在 `.specs__tab .num` 規則（`site.css` 約第 464 行）後面加空狀態樣式

在這一行之後：

```css
.specs__tab .num { font-family: var(--font-mono); font-size: 10px; opacity: 0.7; display: block; }
```

新增：

```css
.specs__tab--empty { cursor: not-allowed; opacity: 0.5; }
.specs__tab--empty:hover { color: var(--fg-muted); }
```

### Step 2: 在 `.specs__note` 規則（`site.css` 約第 477 行）後面加規格列樣式

在這一行之後：

```css
.specs__note { font-size: 12px; color: var(--sage-700); }
```

新增：

```css
.spec-group .pcard__body { gap: 14px; }
.spec-rows { display: flex; flex-direction: column; gap: 12px; }
.spec-row {
  display: flex; justify-content: space-between; align-items: flex-end; gap: 16px;
  padding: 14px 0; border-top: 1px solid rgba(107,125,82,0.12);
}
.spec-rows .spec-row:first-child { border-top: none; padding-top: 0; }
.spec-row__name { font-family: var(--font-serif-cjk); font-size: 16px; font-weight: 600; color: var(--fg-strong); margin: 0 0 6px; }
.spec-row__actions { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }
```

不使用 `transparent`（iPadOS 15 Safari 限制），這裡全部是純色/half-alpha rgba border，符合既有慣例。

### Step 3: 啟動前端 dev server，確認沒有編譯錯誤

```bash
cd frontend && npm run dev
```

Expected: 終端機顯示 dev server 已啟動（`Local: http://localhost:8080/`），無編譯錯誤。之後留給 Task 3 用瀏覽器實際驗證畫面。

### Step 4: Commit

```bash
git add frontend/assets/site.css
git commit -m "style(front): add empty-tab and compact spec-row styles for group tabs"
```

---

## Task 3: 瀏覽器手動驗證 + build/test 檢查

**Files:** 無新增/修改檔案，本任務只驗證 Task 1、2 的結果。

**Interfaces:**
- Consumes：Task 1（`SpecGroupTabs.jsx`、`App.jsx`）、Task 2（`site.css`）的最終結果。
- Produces：無。

### Step 1: 前端建置檢查

```bash
cd frontend && npm run build
```

Expected: 建置成功（`frontend/dist` 產出），無錯誤。

### Step 2: 既有測試檢查

```bash
cd frontend && npm run test
```

Expected: `pricing.test.js`、`notifications.test.js` 等既有測試全數通過（本次改動不涉及這些檔案，用來確認沒有連坐失敗）。

### Step 3: 瀏覽器手動驗證

背景啟動後端與前端：

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

用瀏覽器打開 `http://localhost:8080`，逐項確認：

1. 商店區塊只顯示一組卡片（不再是 3 張並排），預設 active tab 是「箱裝」。
2. 點「兩粒裝」tab：圖片輪播換成兩粒裝那組照片，下方規格列表變成「2粒精緻禮盒」一列。
3. 切回「箱裝」tab：規格列表變回「5 台斤家庭箱」「10 台斤大箱」兩列，圖片輪播換回箱裝那組照片。
4. 箱裝 tab 下，兩個規格分別調整數量、分別按「加入購物車」，購物車（右上角開啟）正確顯示兩筆不同品項並各自累加。
5. 兩粒裝規格的數量 +/− 以 2 為單位遞增遞減（1 → 2 → 4 → 6…），不會出現奇數。
6. 若後台把某規格設為售完：該列數量 stepper 隱藏，按鈕文字變「已售完」且不可點。
7. 輪播圖片 > 1 張時自動輪播、手動點 dots 可切換，且不會把整個頁面捲動（沿用原本的 `scrollToSlide`，只捲動輪播內部）。
8. 縮小瀏覽器視窗模擬 iPad 寬度（約 810px），版面不跑版，Tab 與規格列文字不重疊。

任何一項不符預期，回頭修正 Task 1／2 對應的程式碼，重新驗證，不要跳過。

### Step 4: 更新本計畫與設計文件的完成狀態

在 `docs/superpowers/plans/2026-08-08-storefront-spec-group-tabs.md`（本檔案）把已完成的 Task 勾選為 `- [x]`，並 commit：

```bash
git add docs/superpowers/plans/2026-08-08-storefront-spec-group-tabs.md
git commit -m "docs: mark spec-group-tabs plan complete"
```

---

## 完成後檢查清單（對照 spec）

- [ ] `SpecGroupTabs.jsx` 依 `isTwoPack` 分組，取代 `SpecCard.jsx` 逐一渲染。
- [ ] Tab 預設 active 為箱裝；箱裝為空時 fallback 到第一個非空群組。
- [ ] 空群組 tab 顯示但不可點擊，標示「無商品」。
- [ ] 規格列表維持多規格各自加入購物車互動（方案 A）。
- [ ] 售完 disabled、兩粒裝雙數限購邏輯原樣保留。
- [ ] 購物車、`pricing.js`、`addToCart` 資料形狀未變動。
- [ ] `npm run build`、`npm run test` 通過，瀏覽器手動驗證全項通過。
