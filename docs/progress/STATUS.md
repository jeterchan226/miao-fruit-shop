# 開發進度快照

格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。

## 系統現況

（每完成一個 ticket，用 1–3 句更新系統目前能做什麼。）

訂單品項保存包裝類型快照：既有訂單品項的層數與雙數檢查不受規格改動或刪除影響，後台試算讀同一份快照。

## 已完成

| # | 標題 | OpenSpec change | 完成日 | 紀錄 |
|---|---|---|---|---|
| 46 | 訂單品項快照加入「是否兩粒裝」 | `add-order-item-pack-snapshot` | 2026-10-30 | [紀錄](tickets/46-add-order-item-pack-snapshot.md) |

## 留待之後

| 項目 | 來源 ticket | 備註 |
|---|---|---|
| 雙數錯誤訊息用規格現況名稱，非訂單快照名稱 | #46 | 可併入 #45 |
| GLOSSARY「包裝類型建立後不變」與 admin-catalog 可改的落差 | #46 | design.md Non-Goal |
| ADR 0003／0004 未提包裝類型快照 | #46 | 補一句即可 |

## 下一步建議

- 部署 #46：先跑 migration，立刻部署後端，再部署前端。
