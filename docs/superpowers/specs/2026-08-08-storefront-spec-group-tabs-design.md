# 前台商品呈現改版：包裝群組 Tabs — 設計

## 背景

前台目前把每個 `spec` 渲染成一張獨立的 `SpecCard`（各自輪播圖 + 名稱/內容/價格/購買按鈕），共 3 張卡片並排。後端已在 [2026-07-27-spec-photo-groups](2026-07-26-spec-photo-groups-design.md) 把商品照片依 `is_two_pack`（兩粒裝／箱裝）分組管理，但前台沒有跟著調整，所以畫面看起來跟改版前一模一樣——每張卡仍各自顯示同一群組的重複照片。

參考 [hometownfruit.com 商品頁](https://www.hometownfruit.com/products/info.php?id=82487) 的呈現方式（單一圖片輪播 + 規格選擇），使用者希望把「兩粒裝」「箱裝」當成兩類，各自共用一組圖片，圖片不再依規格重複。

## 目標

- 商店區塊改成「兩粒裝／箱裝」兩個 Tab，切換時只換圖片輪播 + 規格清單。
- 同一 Tab 內的規格改成緊湊列表（非各自一張大卡），維持「可對多個規格分別按加入、同時放進購物車」的現有互動（brainstorming 已選定方案 A）。
- 售完 disabled、兩粒裝雙數限購（`step=2`）、庫存文案等既有規則原樣保留。

## 非目標

- 不改後端 API、不改 `spec.images` 分組邏輯（已完成）。
- 不改購物車（`Cart.jsx`）、`pricing.js`、`addToCart` 的資料形狀。
- 不做多商品目錄（仍是單一商品「甘露梨」，Tab 只是同一商品內的呈現分組）。
- 不新增元件測試（沿用專案慣例：UI 互動用瀏覽器手動驗證）。

## 架構

在 `App.jsx` 商店區塊，把目前：

```jsx
products.flatMap(p => p.specs.map(spec => <SpecCard key={..} p={p} spec={spec} onAdd={addToCart} />))
```

改成：

```jsx
products.map(p => <SpecGroupTabs key={p.id} product={p} onAdd={addToCart} />)
```

新增 `frontend/src/SpecGroupTabs.jsx`，內部把 `product.specs` 依 `spec.isTwoPack` 分成兩組：

```js
const GROUPS = [
  { key: 'box',     label: '箱裝',   filter: s => !s.isTwoPack },
  { key: 'twopack', label: '兩粒裝', filter: s => s.isTwoPack },
];
```

- 預設 active tab：`box`（規格較多、目前主力）。**例外**：若 `box` 群組當下 0 筆規格而 `twopack` 有規格，初始 active 改為第一個非空群組，避免使用者一進頁面就卡在空 Tab（brainstorming 只決定了「一般情況預設 box」與「空群組仍顯示 Tab」，這個 fallback 是兩者疊加後補的邊界情況，實作時一併處理）。
- 群組圖片：取該群組第一筆規格的 `spec.images`（同群組所有規格圖片相同，是後端分組保證的前提）。
- 切換 Tab 只換右側/下方內容，不重新請求資料（`product.specs` 已一次拿齊）。

## 元件拆分

`SpecGroupTabs.jsx` 內含三個部分（同一檔案內的小函式，不另外拆檔——規模小，拆檔案是過度設計）：

1. **Tab bar**：沿用既有但目前未使用的 `.specs__tabs` / `.specs__tab` / `.is-active` CSS（`site.css` 已定義，只是先前沒有元件用到）。空群組的 tab 加 `.specs__tab--empty`：不可點擊、tab 文字旁附「無商品」小字。
2. **GroupCarousel**：把 `SpecCard.jsx` 現有的輪播邏輯（`imgIdx`／`slidesRef`／自動輪播 timer／dots）原樣搬過來，吃 `images` + `season` prop。用 `key={activeGroup.key}` 掛在外層，切換 Tab 時靠 React remount 重置輪播狀態（不用手動處理 timer 清理跨 tab 的邊界情況）。
3. **SpecRow**：把 `SpecCard.jsx` `.pcard__body` 以下（名稱、內容、備註、庫存、雙數限購提示、qty stepper、加入購物車按鈕）的邏輯搬過來，改成清單中的一列而非卡片主體。每個群組下有 N 個 `SpecRow`，各自獨立管理自己的 `qty` state（跟目前 `SpecCard` 一樣，一個 spec 一份 qty state）。

沿用的 CSS class：`.pcard__carousel/__slides/__slide/__season/__dots`（輪播）、`.qty`、`.price`、`.stock`、`.btn`。新增：`.spec-group`（外層容器，套用現有 `.pcard` 卡片樣式）、`.spec-row`（新的緊湊列布局，取代原本整張卡的 `.pcard__body`）、`.specs__tab--empty`。

`SpecCard.jsx` 改版後不再有任何引用者，直接刪除。

## 邊界情況

| 情況 | 行為 |
|---|---|
| 群組 0 筆規格 | Tab 顯示但標示「無商品」，不可點擊切換過去（沿用上面 fallback，避免預設卡在空群組） |
| 規格售完（`stock==='out'`） | 該列 qty stepper 隱藏、按鈕文字「已售完」且 disabled（沿用現有邏輯，不變） |
| 兩粒裝規格 | qty 以 2 為 step，購買單位提示文案不變（沿用現有邏輯） |
| 圖片為空陣列 | 顯示既有的 `.pcard__slide--empty` 空狀態（沿用現有邏輯） |

## 測試 / 驗證

專案前端沒有元件層級單元測試慣例，本次改動不新增假測試。驗證方式：

1. `cd frontend && npm run build` — 確認編譯成功。
2. `cd frontend && npm run test` — 確認 `pricing.test.js`／`notifications.test.js` 等既有純函式測試仍通過（不涉及本次改動，但確認沒有連坐失敗）。
3. 瀏覽器手動驗證（dev server）：
   - 兩個 Tab 都能切換，圖片輪播各自正確、自動輪播與 dots 點擊都正常。
   - 箱裝 Tab 下兩個規格（5 台斤／10 台斤）可分別調整數量、分別加入購物車，購物車正確累加/顯示。
   - 兩粒裝規格 qty 以 2 為單位遞增遞減，加入購物車文案正確。
   - 若有售完規格，該列顯示「已售完」且不可加購。
   - 手動把某群組規格暫時清空（改測試資料或前端 mock）確認空 Tab 呈現「無商品」且不可切入。
   - iPad Safari（或縮小視窗模擬）版面不跑版。
