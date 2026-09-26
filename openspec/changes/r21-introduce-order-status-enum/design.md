## Context

`orders.status` 在 DB 是 `VARCHAR`，沒有 CHECK constraint。

## Goals / Non-Goals

**Goals:** 程式內狀態值只有一個定義點，mypy 能攔截錯字。

**Non-Goals:** 不改 DB 欄位為 Postgres ENUM（變更成本高且 Alembic 對 enum 修改支援差）。

## Decisions

- **`StrEnum`，而非 SQLAlchemy `Enum` 型別**：model 仍映射為 `str`，但以 `Mapped[OrderStatus]` 搭配 `String` 欄位，讀寫皆為字串；不需 migration。
- 可選：另外加 DB `CHECK (status IN (...))` constraint 作為防線；列入 Open Questions，不在本 change 必做。
- 轉移表型別改為 `dict[OrderStatus, frozenset[OrderStatus]]`。

## Risks / Trade-offs

- [DB 已有非預期的狀態值] → 讀入 `Mapped[OrderStatus]` 時 SQLAlchemy 不會驗證（仍為 `String`），不會中斷；以一次性 SQL 查詢確認。

## Open Questions

- 是否要加 DB CHECK constraint？
