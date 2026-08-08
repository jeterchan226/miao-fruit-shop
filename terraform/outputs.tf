output "service_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "cloudsql_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "artifact_registry_repo" {
  value = google_artifact_registry_repository.cloud_run_source_deploy.name
}

output "gcs_bucket" {
  value = google_storage_bucket.product_images.name
}

output "run_runtime_service_account" {
  value = google_service_account.run_runtime.email
}

output "next_steps" {
  value = <<-EOT
    1. gcloud secrets versions add line-channel-access-token --project=${var.project_id} --data-file=- <<< "<token>"
       gcloud secrets versions add line-channel-secret        --project=${var.project_id} --data-file=- <<< "<secret>"
    2. 首次真正部署程式碼(取代 placeholder image):
       cd backend && PROJECT=${var.project_id} REGION=${var.region} ./deploy.sh
    3. uv run python -m app.cli create-admin --username admin(對正式 DB 建管理員)
    4. 前端 Vercel 環境變數改指向新 service_url,見 CLAUDE.md 部署段落
  EOT
}
