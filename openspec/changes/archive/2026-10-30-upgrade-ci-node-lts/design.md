## Context

CI 前端 job 以 `actions/setup-node` 釘 `node-version: "20"`，repo 內沒有 `.nvmrc` 或 `engines`。Vercel 的 Node 版本只在專案設定裡，repo 看不到。部署為手動（ADR 0002），`vercel.json` 的 install/build 指令對根目錄下 `--prefix frontend`。

現行相依的 engines 下限：vite 8、rolldown、@vitejs/plugin-react 要求 `^20.19.0 || >=22.12.0`，vitest 4 要求 `^20.0.0 || ^22.0.0 || >=24.0.0`，22 與 24 皆相容。

2026-10-30 在 Node 24.22 / npm 11.19 上以 `git archive` 匯出的乾淨副本實測：

| 指令 | 結果 |
|---|---|
| 在 `frontend/` 內 `npm ci` | 成功 |
| 在 `frontend/` 內 `npm test` | 106 tests 通過 |
| 在 `frontend/` 內 `npm run build` | 成功 |
| 在根目錄 `npm install --prefix frontend`，再 `npm test` / `npm run build --prefix frontend` | 成功（即 Vercel 的 install/build 指令） |
| `npm ci --prefix <dir>` | 撰寫 spec 時一度失敗（`EUSAGE`，`Missing: frontend@0.1.0 from lock file`）；實作時在 worktree 與乾淨副本的 `--prefix frontend` 皆成功，未重現 |

## Goals / Non-Goals

**Goals:**

- CI 與 Vercel 使用同一個、仍受支援的 Node LTS，版本只宣告一處。
- CI 前端 job 依 lockfile 安裝。

**Non-Goals:**

- `frontend/Dockerfile` 的 `node:22-alpine`：Vercel 部署不經過它，22 也仍在支援期內。
- `vercel.json` 的 `installCommand`：實測在 Node 24 下可用，維持不變。
- 升級前端相依或新增 CD（ADR 0002）。
- 後端 Python 版本。

## Decisions

**Node 24，而非 22。** Node 22 於 2027-04 EOL，只剩約半年，選它會很快重開同一張 ticket；Node 24 支援到 2028-04。Node 26 剛進入 LTS，ticket 範圍也只列 22 / 24，不採用。

**以根目錄 `package.json` 的 `engines.node: "24.x"` 為單一來源。** Vercel 讀 Root Directory 下 `package.json` 的 `engines.node`，且優先於專案設定；`actions/setup-node` 以 `node-version-file: package.json` 讀同一欄位。一致性由結構保證，不靠人工比對 Vercel 後台。替代方案 `.nvmrc`：Vercel 不保證讀取，仍要另外同步。替代方案只把 Vercel 後台改成 24：版本留在 repo 外，正是這張 ticket 要解決的問題。

**CI 前端 job 用 `defaults.run.working-directory: frontend`，指令改為 `npm ci`、`npm test`、`npm run build`。** `--prefix` 的行為在實測中不一致（見 Context），改在 `frontend/` 內執行，與 lockfile 所在目錄一致，也與 `CLAUDE.md` 的本機指令相同。`node-version-file` 由 action 讀取，路徑相對 repo 根目錄，不受 `defaults.run` 影響。

## Testing Decisions

Test entry point 是 **CI 前端 job 本身**，這是現有且最高的 seam：spec 的行為就是 CI 與 build 的結果，HTTP API、domain function、service、DB constraint 四種 seam 都碰不到，不另寫測試程式。Prior art：`.github/workflows/ci.yml` 現有前端 job、`frontend/src` 既有的 vitest 測試。

- `CI 使用宣告的 LTS 版本`：PR 的 CI log 顯示 Node v24。
- `安裝、測試與 build 全數通過`：PR 的 CI 前端 job 綠燈。
- `lockfile 不同步時失敗`：在 lockfile 不同步的情況下本機跑 `npm ci` 確認失敗；不需在 CI 留下失敗提交。
- `Vercel build 與 CI 版本一致`：Vercel build log 顯示的 Node 版本，結果記入 ticket 進度紀錄。

各 slice 的「failing test」是改動前會失敗的檢查指令，見 `tasks.md`。

## Risks / Trade-offs

- [Vercel 專案的 Root Directory 不是 repo 根目錄，根目錄的 `engines` 不生效] → 看 Vercel build log 的 Node 版本確認；repo 內無法驗證此設定。若不是 24，改把 `engines` 放到 Root Directory 對應的 `package.json`，CI 的 `node-version-file` 指向同一檔。
- [Vercel 不支援 24.x 或後續下架] → 同樣由 build log 發現；Vercel 會在 build 時失敗而非靜默換版，回退為改 `engines` 一行。
- [`engines` 在下次部署才生效，第一次用 Node 24 build 就是正式部署] → 依 ADR 0002 部署仍手動，若有 preview deployment 先看其 build log；出問題 `vercel rollback`。
- [本機實測用 npm 11.19，CI 隨 Node 24 帶的 npm 版本可能不同] → CI 前端 job 本身會驗證，失敗時 PR 擋下。
