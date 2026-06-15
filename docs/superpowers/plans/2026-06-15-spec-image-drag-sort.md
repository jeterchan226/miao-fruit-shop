# Spec Image Drag Sort Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在後台規格圖片 Gallery 中加入拖曳排序功能，支援桌機滑鼠與觸控裝置。

**Architecture:** 使用 @dnd-kit/core + @dnd-kit/sortable 在 `SpecImageGallery` 元件中加入 DnD 支援。新增 `SortableImageItem` 子元件封裝 `useSortable` hook，`onDragEnd` 以樂觀更新方式更新本地 state 後呼叫已存在的後端 API。

**Tech Stack:** React 18, @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities, Vite

---

## 檔案異動對照

| 檔案 | 動作 | 說明 |
|---|---|---|
| `frontend/package.json` | 修改 | 新增三個 @dnd-kit 套件 |
| `frontend/src/AdminApp.jsx` | 修改 | import 更新、新增 `SortableImageItem`、改寫 `SpecImageGallery` |
| `frontend/assets/admin.css` | 修改 | 補 drag handle 與 dragging 狀態樣式 |

---

### Task 1：建立 Branch 並安裝套件

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1：從 master 建立新 branch**

```bash
git checkout master
git checkout -b feat/admin-spec-image-drag-sort
```

- [ ] **Step 2：安裝 @dnd-kit 套件**

```bash
cd frontend
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

預期 `package.json` 的 `dependencies` 新增三個 `@dnd-kit/*` 項目。

- [ ] **Step 3：確認安裝成功**

```bash
npm run build 2>&1 | tail -5
```

預期：`✓ built in` 等成功訊息，無 error。

- [ ] **Step 4：Commit**

```bash
cd ..
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(frontend): install @dnd-kit for drag-sort"
```

---

### Task 2：新增 CSS 樣式

**Files:**
- Modify: `frontend/assets/admin.css:669-692`（`.img-gallery__delete` 到 `.img-gallery__upload-btn` 區段）

- [ ] **Step 1：在 `admin.css` 的 `.img-gallery__item:hover .img-gallery__delete` 那行之後插入拖曳相關樣式**

在 `frontend/assets/admin.css` 找到這一行：
```css
.img-gallery__item:hover .img-gallery__delete { opacity: 1; }
```

在它**之後**插入：

```css
.img-gallery__drag-handle {
  position: absolute; top: 4px; left: 4px;
  color: rgba(255,255,255,0.85);
  font-size: 14px; line-height: 1;
  cursor: grab;
  touch-action: none;
  opacity: 0;
  transition: opacity var(--dur-micro);
  user-select: none;
}
.img-gallery__item:hover .img-gallery__drag-handle { opacity: 1; }
.img-gallery__item--dragging { opacity: 0.4; }
```

- [ ] **Step 2：Commit**

```bash
git add frontend/assets/admin.css
git commit -m "style(admin): add drag handle and dragging state styles"
```

---

### Task 3：實作拖曳排序邏輯

**Files:**
- Modify: `frontend/src/AdminApp.jsx:1-19`（import 區）
- Modify: `frontend/src/AdminApp.jsx:452-519`（`SpecImageGallery` 元件）

- [ ] **Step 1：更新 `AdminApp.jsx` 頂部 import**

將 `AdminApp.jsx` 第 1 行開頭的 import 區段替換為以下內容（在原有 React import 後加入 @dnd-kit import，並在 api.js import 中加入 `reorderSpecImages`）：

```js
/* Admin order management — redesigned 2026-06-14 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  DndContext,
  PointerSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import {
  createSpec,
  deleteProductImage,
  deleteSpec,
  getAdminOrder,
  getCurrentAdmin,
  listAdminOrders,
  listAdminProducts,
  listSpecImages,
  loginAdmin,
  registerSpecImage,
  reorderSpecImages,
  signUpload,
  updateAdminOrderStatus,
  updateSpec,
} from './api.js';
```

- [ ] **Step 2：在 `SpecImageGallery` 之前插入 `SortableImageItem` 元件**

在 `AdminApp.jsx` 找到這行注解：
```js
/* ── Spec image gallery (規格層級) ── */
```

在它**之前**插入以下元件定義：

```jsx
/* ── Sortable image item ── */
function SortableImageItem({ image, onDelete }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: image.id });
  const style = { transform: CSS.Transform.toString(transform), transition };
  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`img-gallery__item${isDragging ? ' img-gallery__item--dragging' : ''}`}
    >
      <span className="img-gallery__drag-handle" {...attributes} {...listeners}>⠿</span>
      <img src={image.url} alt="" className="img-gallery__thumb" />
      <button
        className="img-gallery__delete"
        onClick={() => onDelete(image.id)}
        title="移除"
      >✕</button>
    </div>
  );
}
```

- [ ] **Step 3：改寫 `SpecImageGallery` 元件**

將 `AdminApp.jsx` 中整個 `SpecImageGallery` 函式（從 `function SpecImageGallery` 到結尾的 `}` 共約 67 行，目前在 line 453–519）替換為：

```jsx
/* ── Spec image gallery (規格層級) ── */
function SpecImageGallery({ specId, token }) {
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } }),
  );

  useEffect(() => {
    listSpecImages(token, specId).then(setImages).catch(() => {});
  }, [specId, token]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const { signed_url, public_url } = await signUpload(token, file.name, file.type);
      await fetch(signed_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });
      const img = await registerSpecImage(token, specId, public_url, images.length);
      setImages((prev) => [...prev, img]);
    } catch (err) {
      setError('上傳失敗：' + (err?.message || '請稍後再試'));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (imageId) => {
    try {
      await deleteProductImage(token, imageId);
      setImages((prev) => prev.filter((i) => i.id !== imageId));
    } catch {
      setError('刪除失敗，請稍後再試');
    }
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = images.findIndex((i) => i.id === active.id);
    const newIndex = images.findIndex((i) => i.id === over.id);
    const prevImages = images;
    const newImages = arrayMove(images, oldIndex, newIndex);
    setImages(newImages);
    try {
      await reorderSpecImages(
        token,
        specId,
        newImages.map((img, idx) => ({ id: img.id, sort_order: idx })),
      );
    } catch {
      setImages(prevImages);
      setError('排序儲存失敗，請稍後再試');
    }
  };

  return (
    <div className="img-gallery">
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={images.map((i) => i.id)} strategy={rectSortingStrategy}>
          <div className="img-gallery__grid">
            {images.map((img) => (
              <SortableImageItem key={img.id} image={img} onDelete={handleDelete} />
            ))}
            <label className={`img-gallery__upload-btn${uploading ? ' is-uploading' : ''}`}>
              {uploading ? '上傳中…' : '＋'}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={handleFileChange}
                disabled={uploading}
              />
            </label>
          </div>
        </SortableContext>
      </DndContext>
      {error && <div className="adm-alert" style={{ marginTop: 8 }}>{error}</div>}
    </div>
  );
}
```

- [ ] **Step 4：確認 build 無錯誤**

```bash
cd frontend
npm run build 2>&1 | tail -10
```

預期：`✓ built in` 等成功訊息，無 error 或 warning。

- [ ] **Step 5：Commit**

```bash
cd ..
git add frontend/src/AdminApp.jsx
git commit -m "feat(admin): add drag & drop reorder for spec images"
```

---

### Task 4：手動驗收

> 在本機啟動後台開發伺服器進行驗收。

- [ ] **Step 1：啟動 dev server**

```bash
cd frontend
npm run dev
```

在瀏覽器開啟 `http://localhost:8080/admin`，登入後台。

- [ ] **Step 2：驗收桌機拖曳**

1. 進入「商品」頁籤 → 點選任一規格的「編輯規格」
2. 在規格彈窗中確認圖片 Gallery 顯示 `⠿` handle（hover 才出現）
3. 拖曳圖片至不同位置，確認 UI 即時更新
4. 重新整理頁面，確認新順序保留

- [ ] **Step 3：驗收觸控（行動裝置或 DevTools 模擬）**

1. 開啟 Chrome DevTools → Toggle Device Toolbar（Ctrl/Cmd+Shift+M）
2. 選擇任意行動裝置模擬
3. 長按圖片 200ms 後拖曳，確認觸控拖曳可用

- [ ] **Step 4：驗收刪除與上傳不受影響**

1. 上傳新圖片，確認新增成功
2. 刪除圖片，確認刪除成功

- [ ] **Step 5：驗收錯誤還原（可選）**

暫時將 `reorderSpecImages` 改為拋出錯誤，驗證 UI 能還原排序並顯示錯誤訊息後還原。

---

## 驗收條件對照（來自設計文件）

- [ ] 桌機：可用滑鼠拖曳圖片至任意位置，排序持久化到後端
- [ ] 觸控：可長按 200ms 後拖曳，排序持久化到後端
- [ ] 拖曳過程中有視覺回饋（半透明 + handle 圖示）
- [ ] API 失敗時 UI 還原並顯示錯誤訊息
- [ ] 刪除與上傳功能不受影響
- [ ] 不引入 @dnd-kit 以外的新 dependency
