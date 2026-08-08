resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com", # gcloud run deploy --source 需要
    "storage.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com", # SA 簽 GCS signed URL 需要
  ])
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}
