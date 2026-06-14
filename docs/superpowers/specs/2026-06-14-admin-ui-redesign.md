# Admin UI Redesign — Design Spec

**Date:** 2026-06-14
**Scope:** 重新設計 `frontend/src/AdminApp.jsx` 與 `frontend/assets/admin.css`，讓後台視覺風格與前台商店統一，並改為全幅表格 + 置中 Modal 版面。後端 API 合約不變。

---

## 1. 設計決策摘要

| 項目 | 決策 |
|------|------|
| 整體風格 | 白底主體 + 深 Sage 頂欄（Option B — 輕量現代） |
| 表格版面 | 全幅（移除右側 sticky 側邊欄） |
| 明細呈現 | 置中 Dialog Modal（Option A） |
| 篩選列 | Chip 狀態切換 + 統一搜尋框 + 日期區間（Option B） |

---

## 2. Design Tokens

直接沿用 `assets/colors_and_type.css` 的既有 token，不新增額外 CSS 變數。

| 角色 | Token | 值（參考） |
|------|-------|-----------|
| 頁面背景 | `--cream-soft` | `#F1DDB4` → 使用 `#F8F5F0`（略淡） |
| 頂欄背景 | `--sage-900` | `#4F5C3D` |
| 頂欄文字 | `--sage-200` | `#D2DBBC` |
| 主要按鈕 | `--sage-900` bg + `--cream-card` text | |
| 表格 header | `white` bg + `--brown-500` text | |
| 表格 hover | `--cream-card` `#FDF6E5` | |
| Badge 顏色 | 見 §5 | |
| 字型 | `--font-sans-cjk`（Noto Sans TC）主體；`--font-serif-cjk`（Noto Serif TC）頁面標題；`--font-mono`（IBM Plex Mono）訂單編號 |
| Shadow | `--shadow-2` Modal；`--shadow-1` 表格卡片 |

---

## 3. 版面結構

```
┌─────────────────────────────────────────────┐
│  Topbar  (height: 52px, bg: #4F5C3D)        │
│  Logo · Nav(訂單/商品) · 使用者 + 登出        │
├─────────────────────────────────────────────┤
│  Page Header  (padding: 20px 24px 0)        │
│  「訂單管理」(serif) · 共 N 筆               │
├─────────────────────────────────────────────┤
│  Filter Strip  (padding: 14px 24px)         │
│  [Chip列]  [搜尋框──────────] [起日] — [迄日]│
├─────────────────────────────────────────────┤
│  Table  (全幅, margin: 0 24px)              │
│  thead: white bg, brown-500, 2px border     │
│  tbody: white, hover #FDF6E5                │
│  pagination bar                             │
└─────────────────────────────────────────────┘
                   ↕ (Modal 疊加時)
┌──────── 遮罩 rgba(30,22,14,.6) + blur(2px) ────────┐
│  ┌──────────────── Modal (640px) ──────────────┐   │
│  │ Header: 訂單號(mono) · 客戶名 · 狀態Badge · ✕ │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Body (2-col grid):                          │   │
│  │  左：收件資訊 dl                             │   │
│  │  右：商品明細 + 小計/運費/手續費/總計         │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Footer: 「變更狀態」label · select · 確認更新 │   │
│  └─────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

---

## 4. 元件規格

### 4.1 Topbar

- 高度 52px，`background: var(--sage-900)` (`#4F5C3D`)
- **Logo**：`font-family: var(--font-serif-cjk)`，16px，`color: #E6EBD7`
- **Nav**：訂單管理 / 商品管理（目前商品管理為 placeholder，不連結）。Active 狀態：白色文字 + `rgba(255,255,255,.12)` 背景。
- **使用者區**：username（灰色）+ 登出按鈕（ghost style，border `rgba(255,255,255,.15)`）

### 4.2 Chip 篩選列

- 第一列：狀態 Chip 組
  - 選項：全部 / 待付款 / 待確認 / 已確認 / 出貨中 / 已送達 / 已取消
  - 每個 chip **不顯示獨立計數**（後端無 per-status summary endpoint）；「全部」chip 顯示 `orders.total`（當前未篩選時的總數）
  - **Active chip**：`background: var(--sage-900)`，白色文字
  - **Inactive chip**：白底，`border: 1px solid #D2DBBC`，`color: var(--brown-700)`
  - 點擊 chip → 立即呼叫 `loadOrders(1, { status: value })`，不需額外按查詢
- 第二列：搜尋框 + 日期區間
  - **搜尋框**：`flex: 1`，placeholder `搜尋姓名、電話、訂單編號…`，leading search icon (SVG)，輸入後 300ms debounce 觸發搜尋
  - **日期起迄**：兩個 `type="date"` input，中間 `—` 分隔，寬 120px 各

> 注意：搜尋框輸入規則 — 若輸入值符合 `/^MM-/i` 正規式，送 `order_no` 參數（精確比對）；否則送 `q` 參數（姓名 + 電話 ilike 搜尋）。Chip 狀態與搜尋框為獨立 filter，可同時作用。

### 4.3 訂單表格

- 外層包 `border-radius: 10px`，`box-shadow: var(--shadow-1)`，`background: white`，`overflow: hidden`
- 欄位（從左到右）：訂單編號 · 狀態 · 收件人 · 電話 · 金額（右對齊）· 建立時間
- **thead**：white bg，`font-size: 11px`，`font-weight: 700`，`color: var(--brown-500)`，`letter-spacing: .06em`，`text-transform: uppercase`，底部 `2px solid #F0E8DA`
- **tbody row**：hover 背景 `#FDF6E5`，cursor pointer；選中列（已開啟 Modal）背景 `#F5EDE0`
- **訂單編號**：`font-family: var(--font-mono)`，`color: var(--sage-700)`
- **電話、時間**：`color: var(--brown-500)` muted
- **分頁列**：表格下方，左側「第 N 頁，共 M 頁」，右側 ← 上一頁 · 頁碼 · 下一頁 →

### 4.4 狀態 Badge

每個 badge 帶一個前綴色點（`6px` 圓形），語意配色：

| 狀態 | 背景 | 文字 | 色點 |
|------|------|------|------|
| pending_payment / pending | `#FFF3CD` | `#856404` | `#D9923B` |
| confirmed | `#D1E7DD` | `#0f5132` | `#198754` |
| shipping | `#CFE2FF` | `#084298` | `#0d6efd` |
| delivered | `#D1E7DD` | `#0f5132` | `#6B7D52` |
| cancelled | `#F8D7DA` | `#842029` | `#C24A3A` |

### 4.5 訂單明細 Modal

**開啟方式**：點擊表格列 → 呼叫 `getAdminOrder(token, orderNo)` → 資料載入後顯示 Modal

**關閉方式**：點擊遮罩 / 點 ✕ 按鈕 / 按 Escape 鍵

**遮罩**：`position: fixed; inset: 0; background: rgba(30,22,14,.6); backdrop-filter: blur(2px)`

**Modal 容器**：
- `width: min(640px, 90vw)`
- `max-height: 85vh`，body 部分 `overflow-y: auto`
- `border-radius: 12px`
- `box-shadow: var(--shadow-3)`

**Modal Header**（`background: #FDFAF4`）：
- 左：訂單號（mono 11px sage green）+ 客戶名（18px bold）
- 右：狀態 Badge + ✕ 關閉按鈕（28px 圓形，`background: #F0E8DA`）

**Modal Body**（`display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px`）：
- 左欄：收件資訊 `<dl>`（dt/dd 64px/1fr grid，含：電話、Email、地址、希望送達、配送時段、付款方式、備註）
- 右欄：商品明細列表 + 小計/運費/貨到付款手續費/總計

**Modal Footer**（`background: #FDFAF4`，`border-top: 1px solid #E6EBD7`）：
- `變更狀態` label + select（顯示合法下一狀態，若無則 disabled）+ 「確認更新」按鈕
- 更新成功後：關閉 Modal、重新整理列表、toast 通知（選填）

**載入狀態**：Modal 開啟後顯示 skeleton 佔位，資料到後 fade in

---

## 5. 互動行為

### 篩選與搜尋

- Chip 點擊 → 立即（0ms）呼叫 `loadOrders(1)`
- 搜尋框輸入 → 300ms debounce 後呼叫 `loadOrders(1)`
- 日期 input change → 立即呼叫 `loadOrders(1)`
- 所有篩選條件共同維護在同一個 `filters` state object

### Modal

- 點列 → 設定 `selectedOrderNo` → `loadDetail(orderNo)` → Modal 顯示
- `Escape` 鍵關閉（`useEffect` 監聽 keydown）
- 更新狀態 → `updateAdminOrderStatus` → 成功後更新 `detail` state + 重新載入列表 → Modal 留開（顯示新狀態）
- 若 API 返回 409 → Modal 內顯示 error message（不關閉）

### 錯誤處理

- 列表載入失敗 → 表格上方 error bar（`packaging-red` 色系）
- Modal 明細載入失敗 → Modal body 顯示 error state + retry 按鈕
- 401 → 自動登出，跳回登入頁

### 登入頁

- 樣式同 Option B 語言：白卡片 + 深 Sage 頂部裝飾條或 brand eyebrow
- 欄位標籤 + input + 登入按鈕（sage-900 primary）
- 錯誤用 inline alert（紅色 border + 淡紅背景）

---

## 6. 檔案異動

| 檔案 | 異動類型 | 說明 |
|------|----------|------|
| `frontend/src/AdminApp.jsx` | 全改寫 | 新版 UI 邏輯 + 元件 |
| `frontend/assets/admin.css` | 全改寫 | 新版 CSS（沿用 colors_and_type.css tokens） |

`api.js`、`main.jsx`、`colors_and_type.css` 均不改動。

---

## 7. 不在本次範圍內

- 商品管理頁（Nav 顯示但不連結）
- 訂單匯出 / 列印功能
- 深色模式
- RWD 手機版（保留現有 media query 即可，不做積極優化）
