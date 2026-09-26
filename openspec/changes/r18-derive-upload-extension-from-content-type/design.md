## Context

`schemas/image.py` 的 `_ALLOWED_CONTENT_TYPES` 已是允許清單；副檔名對照可以與它共用同一個來源。

## Goals / Non-Goals

**Goals:** 副檔名與內容類型一致，且只有一份對照表。

**Non-Goals:** 不檢查上傳內容的實際 magic bytes（瀏覽器直傳 GCS，後端看不到內容）。

## Decisions

- 定義 `CONTENT_TYPE_EXTENSIONS: dict[str, str]` 於 `core/constants.py`，`_ALLOWED_CONTENT_TYPES` 改為 `CONTENT_TYPE_EXTENSIONS.keys()`，避免兩份清單漂移。
- `sign_upload` 改接收 `content_type` 決定副檔名；`filename` 參數移除於 service 層，但 schema 保留欄位以免前端 422。

## Risks / Trade-offs

- [前端上傳 HEIC 等格式] → 已被既有 schema 拒絕，行為不變。
- 與 r17 修改同一函式，建議同一 PR 或依序實作。
