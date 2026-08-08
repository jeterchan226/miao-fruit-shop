# Cloud Run 執行用 SA(取代 default compute SA,權限最小化)。
resource "google_service_account" "run_runtime" {
  project      = var.project_id
  account_id   = "miao-api-runtime"
  display_name = "miao-api Cloud Run 執行帳號"
}

resource "google_project_iam_member" "run_runtime_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "db_password_access" {
  secret_id = google_secret_manager_secret.db_password.secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "jwt_secret_access" {
  secret_id = google_secret_manager_secret.jwt_secret.secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "gcs_credentials_access" {
  secret_id = google_secret_manager_secret.gcs_credentials_b64.secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "line_token_access" {
  secret_id = google_secret_manager_secret.line_channel_access_token.secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "line_secret_access" {
  secret_id = google_secret_manager_secret.line_channel_secret.secret_id
  project   = var.project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run_runtime.email}"
}

# 商店 API 對外公開(前端直接呼叫,無 auth header),用 CORS 白名單擋,不用 IAM 擋。
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
