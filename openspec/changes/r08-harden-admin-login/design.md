## Context

後台只有少數管理員，帳號名稱可猜（`admin`）。目前 argon2 雜湊可減緩線上嘗試，但沒有上限。Cloud Run 可能同時有多個 instance，in-memory 狀態無法共享。

## Goals / Non-Goals

**Goals:** 讓線上暴力破解不可行；鎖定狀態跨 instance 一致；避免弱 JWT 金鑰。

**Non-Goals:** 不做 2FA、不做 refresh token、不改 token 儲存位置；IP 節流不跨 instance 共享。

## Decisions

- **帳號鎖定存於 `admin_users`（`failed_login_count INT NOT NULL DEFAULT 0`、`locked_until TIMESTAMPTZ NULL`）**，而非另建 `login_attempts` 表：只需要「目前連續失敗次數」，不需要歷史，兩個欄位即可。
- **IP 節流仍用 `slowapi` in-memory**（與 r02 共用 `app/core/rate_limit.py`）：它的用途是擋下大量請求，放在 DB 反而會讓每次請求都寫 DB。多 instance 下每個 instance 各自計數，可接受。
- **登入流程的 DB 存取：**
  1. `SELECT ... FOR UPDATE` 讀取管理員（原本就要讀，多一個列鎖避免並行失敗計數遺失）。
  2. 若 `locked_until > now()` → 直接回 429，**不寫入**。
  3. 密碼錯誤 → `UPDATE failed_login_count + 1`，達 5 次時同時設 `locked_until`。
  4. 密碼正確 → 只在 `failed_login_count > 0` 或 `locked_until` 不為 null 時才 `UPDATE` 歸零，**一般成功登入不寫入**。
  5. 帳號不存在 → 不寫入（避免攻擊者用任意帳號名灌寫入）。
- 鎖定期間即使密碼正確也拒絕，避免攻擊者從回應差異得知密碼正確；且鎖定期間**不做 argon2 驗證**，同時省下 CPU。
- 時間以可注入的 `now` 函式取得，方便測試鎖定到期。
- `jwt_secret` 用 Pydantic `Field(min_length=32)`；測試與 CI secret 同步使用夠長的值。

## DB I/O 評估

- 正常使用：每次登入 1 次 `SELECT`（本來就有），成功登入通常 0 次寫入。後台管理員一天登入次數個位數，負載可忽略。
- 遭受攻擊：寫入只發生在「存在的帳號 + 密碼錯誤」，每個 IP 每分鐘最多 10 次（被 IP 節流擋住）；帳號鎖定後的請求只讀不寫。即使 10 個 IP 同時攻擊，也只是每分鐘約 100 次單列 `UPDATE`。
- Cloud SQL 最小規格（db-f1-micro / shared-core）可承受每秒數百次簡單單列寫入，上述量級遠低於上限；真正的瓶頸會是 argon2 的 CPU（每次約 50ms），而鎖定後跳過 argon2 反而降低 CPU 負載。
- 連線數：登入沿用既有 request session，不增加連線池使用量。

## Risks / Trade-offs

- [攻擊者故意鎖住管理員帳號（DoS）] → 鎖定 15 分鐘自動解除；可用 `unlock-admin` CLI 立即解鎖。
- [需要 migration] → 新增欄位皆有預設值或可為 null，屬 expand 型變更，舊版程式在 migration 後仍可正常運作，沿用 `deploy.sh` 的流程即可。

## Resolved Questions

- 鎖定狀態改存資料庫以跨 instance 一致（2026-09-26 確認）。
