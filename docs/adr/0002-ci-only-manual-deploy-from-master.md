# 只保留 CI，正式部署手動從 master 執行

單人維護、低頻發版，因此 2026-06-24 移除 tag 觸發的全自動 CD（Cloud Run + Vercel、Workload Identity Federation），只保留 PR / push master 時跑測試與前端 build 的 CI。正式部署一律在變更合併進 master 後手動執行（後端 `gcloud run deploy`、migration job、前端 `vercel --prod`）。

## Considered Options

- 全自動 CD（WIF + release workflow）：設定與權限維護成本高於發版頻率帶來的效益，已實作後撤除，不要再導回。
