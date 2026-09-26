## Context

搜尋欄位：`customer_name`、`customer_phone`、`line_display_name`、`line_user_id`。

## Goals / Non-Goals

**Goals:** 字面比對。

**Non-Goals:** 不做全文搜尋、不加 trigram 索引（訂單量小）。

## Decisions

- 以 `ilike(pattern, escape="\\")`；跳脫函式 `escape_like(s)` 先換 `\` 再換 `%`、`_`，放在 repository 模組（屬查詢細節）。
- 空白修剪在 service 層處理（屬輸入正規化）。

## Risks / Trade-offs

- 無明顯風險。
