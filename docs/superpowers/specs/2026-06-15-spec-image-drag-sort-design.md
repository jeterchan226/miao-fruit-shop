# 規格圖片拖曳排序設計文件

**日期：** 2026-06-15
**功能：** 後台規格圖片拖曳排序（Admin Spec Image Drag & Drop Reorder）
**狀態：** 待實作

---

## 背景

目前 `SpecImageGallery` 元件以靜態 Grid 呈現規格圖片，無排序功能。後端排序 API 已存在（`PATCH /api/admin/specs/{spec_id}/images/reorder`），只需補齊前端拖曳互動。

後台需支援桌機（滑鼠）與行動裝置（觸控），因此選用 `@dnd-kit` 系列套件，原生支援 Pointer / Touch 事件。

---

## 技術選型

- **@dnd-kit/core** — DnD context 與感測器（PointerSensor、TouchSensor）
- **@dnd-kit/sortable** — `SortableContext`、`useSortable` hook
- **@dnd-kit/utilities** — `arrayMove` 工具函式
- **理由：** 觸控支援穩定、React 整合良好、輕量（約 15KB gzipped）；不自製 pointer event 拖曳、不引入已停止維護的 polyfill

---

## 元件結構

```
SpecImageGallery
  └─ div.img-gallery
       └─ DndContext (onDragEnd)
            └─ SortableContext (items=[img.id, ...], strategy=rectSortingStrategy)
                 ├─ SortableImageItem (per image)
                 │    └─ div.img-gallery__item
                 │         ├─ span.img-gallery__drag-handle  ⠿
                 │         ├─ img.img-gallery__thumb
                 │         └─ button.img-gallery__delete
                 └─ label.img-gallery__upload-btn  (不參與排序)
```

`SortableImageItem` 是新增的子元件，封裝 `useSortable`，對外 props：`image`, `onDelete`。

---

## 感測器設定

```js
const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } }),
);
```

- `PointerSensor` 移動 5px 後啟動，避免點擊誤觸
- `TouchSensor` 長按 200ms 啟動，給系統捲軸手勢預留空間

---

## 資料流

```
onDragEnd(event)
  1. 解構 active.id / over.id，若相同則 return
  2. setImages(prev => arrayMove(prev, oldIndex, newIndex))  ← 樂觀更新
  3. 建構 payload: [{ id, sort_order }, ...]（依新陣列順序從 0 起編）
  4. await reorderSpecImages(token, specId, payload)
  5. 失敗時：還原 images state，setError('排序儲存失敗，請稍後再試')
```

不使用 debounce，每次 `onDragEnd` 觸發一次 API。

---

## 視覺行為

| 狀態 | 樣式 |
|---|---|
| 正在拖曳的項目 | `opacity: 0.4`（由 `.img-gallery__item--dragging` 控制） |
| 放置目標位置 | @dnd-kit 的 overlay placeholder（虛線框） |
| Drag handle | 左上角 `⠿` 圖示，`cursor: grab`；拖曳中改為 `grabbing` |
| 觸控元素 | `touch-action: none`（必要，讓 @dnd-kit 接管觸控事件） |

刪除按鈕維持 hover 才顯示（桌機）；觸控裝置維持現有行為。

---

## CSS 新增

在 `frontend/assets/admin.css` 的 `.img-gallery` 區段補上：

```css
.img-gallery__drag-handle {
  position: absolute; top: 4px; left: 4px;
  color: rgba(255,255,255,0.85);
  font-size: 14px; line-height: 1;
  cursor: grab;
  touch-action: none;
  opacity: 0;
  transition: opacity var(--dur-micro);
}
.img-gallery__item:hover .img-gallery__drag-handle { opacity: 1; }
.img-gallery__item--dragging { opacity: 0.4; }
```

---

## 檔案異動清單

| 檔案 | 變更內容 |
|---|---|
| `frontend/package.json` | 新增 `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities` |
| `frontend/src/AdminApp.jsx` | 改寫 `SpecImageGallery`；新增 `SortableImageItem` 元件 |
| `frontend/assets/admin.css` | 補 `__drag-handle`、`__item--dragging` 樣式 |

後端無任何異動。

---

## 驗收條件

- [ ] 桌機：可用滑鼠拖曳圖片至任意位置，排序持久化到後端
- [ ] 觸控：可長按 200ms 後拖曳，排序持久化到後端
- [ ] 拖曳過程中有視覺回饋（半透明 + 放置指示）
- [ ] API 失敗時 UI 還原並顯示錯誤訊息
- [ ] 刪除與上傳功能不受影響
- [ ] 不引入 @dnd-kit 以外的新 dependency
