# gcloud run deploy --source 預設會找/建這個名稱的 repo 來放 build 出來的 image。
# 明確用 Terraform 建,避免第一次跑 deploy.sh 時互動式提示建立 repo。
resource "google_artifact_registry_repository" "cloud_run_source_deploy" {
  project       = var.project_id
  location      = var.region
  repository_id = "cloud-run-source-deploy"
  format        = "DOCKER"
  description   = "gcloud run deploy --source 自動 build 的 image"

  depends_on = [google_project_service.apis]
}
