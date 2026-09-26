## ADDED Requirements

### Requirement: Migration 與 model 一致
CI SHALL 在乾淨資料庫執行所有 Alembic migration 至 head，並以 autogenerate 比對 SQLAlchemy model，若有任何差異 MUST 使測試失敗。

#### Scenario: model 新增欄位但沒有 migration
- **WHEN** 某個 model 新增欄位但沒有對應的 migration
- **THEN** migration 一致性測試失敗，並列出差異

#### Scenario: model 與 migration 一致
- **WHEN** 所有 model 變更都有對應的 migration
- **THEN** 測試通過

### Requirement: Migration 可往返
CI SHALL 驗證 `alembic downgrade base` 後再 `upgrade head` 能成功執行。

#### Scenario: 往返成功
- **WHEN** 在 head 狀態執行 downgrade base 再 upgrade head
- **THEN** 兩個指令皆無錯誤
