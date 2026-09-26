## Context

`frontend/src/api.js` 的請求以 `Authorization` header 帶 JWT；登入使用 `application/x-www-form-urlencoded`（OAuth2PasswordRequestForm），屬 CORS 簡單標頭，不需額外允許。

## Goals / Non-Goals

**Goals:** 最小權限的 CORS 設定。

**Non-Goals:** 不改 origin 白名單與 regex。

## Decisions

- 關閉 credentials；收斂 methods/headers。替代方案「只關 credentials」較保守，但收斂 methods 同樣無功能損失，一併處理。
- 測試以 `httpx` 發送預檢請求斷言標頭。

## Risks / Trade-offs

- [前端某處用 `credentials: 'include'`] → 實作前 grep 確認；若有則移除。
- [未來加入 `PUT` 或自訂 header] → 需同步更新設定，測試會提醒。
