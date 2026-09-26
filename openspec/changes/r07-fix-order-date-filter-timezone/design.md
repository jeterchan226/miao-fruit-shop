## Context

`order_repo.list_filtered` 做 `Order.created_at >= date_from`，SQLAlchemy 送出 `date` 參數，Postgres 以 session TimeZone 轉型。測試 DB 與 Cloud SQL 預設 UTC，所以目前測試看不出問題。

## Goals / Non-Goals

**Goals:** 篩選語意與店家的營業日一致，不受 DB session 時區影響。

**Non-Goals:** 不改 `created_at` 的儲存方式；不改前端日期選擇器。

## Decisions

- **在 Python 端轉成 aware `datetime` 再傳給 SQL**（`datetime.combine(d, time.min, tzinfo=ZoneInfo(tz))`），而非 `SET TIME ZONE` 或 SQL 端 `AT TIME ZONE`：與 DB 設定解耦，也能沿用 `created_at` 索引。
- 轉換函式 `to_business_day_range(date_from, date_to)` 放在 service 層（屬業務規則），repo 只接受 `datetime`。
- 測試以明確的 `created_at` 值插入（覆寫 server_default），並在測試連線上執行 `SET TIME ZONE 'UTC'` 確保可重現。

## Risks / Trade-offs

- [容器缺 tzdata 導致 `ZoneInfo` 失敗] → `python:3.13-slim` 內含 tzdata？不保證；在 `pyproject` 加入 `tzdata` 套件確保可用。
