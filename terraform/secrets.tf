resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

# --- db-password:值由 Terraform 產生,同時寫進 Cloud SQL user 跟 secret,
#     兩邊天生同步,不會再踩「單獨 reset 密碼 → DB API 全 500」那個坑。---
resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "db-password"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "jwt_secret" {
  project   = var.project_id
  secret_id = "jwt-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

# GCS 簽章用 SA key(json),base64 供 app 的 GCS_CREDENTIALS_B64 讀。
resource "google_secret_manager_secret" "gcs_credentials_b64" {
  project   = var.project_id
  secret_id = "gcs-credentials-b64"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "gcs_credentials_b64" {
  secret      = google_secret_manager_secret.gcs_credentials_b64.id
  secret_data = google_service_account_key.gcs_signer_key.private_key # 已是 base64
}

# --- LINE Messaging API 憑證:換帳號時從 LINE Developers Console 複製,
#     Terraform 只建空容器,值用指令灌,不進 tfvars/state。---
resource "google_secret_manager_secret" "line_channel_access_token" {
  project   = var.project_id
  secret_id = "line-channel-access-token"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "line_channel_secret" {
  project   = var.project_id
  secret_id = "line-channel-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

# Cloud Run 建 revision 時 secret_key_ref(latest)要求版本存在,不能指向空 secret。
# 先塞一版佔位,真值用 fill-line-secrets.sh(gcloud secrets versions add)蓋掉——
# 那是額外新增版本,不動這個 terraform 管的 version 1,故不用 ignore_changes。
resource "google_secret_manager_secret_version" "line_channel_access_token_placeholder" {
  secret      = google_secret_manager_secret.line_channel_access_token.id
  secret_data = "unset-run-fill-line-secrets.sh"
}

resource "google_secret_manager_secret_version" "line_channel_secret_placeholder" {
  secret      = google_secret_manager_secret.line_channel_secret.id
  secret_data = "unset-run-fill-line-secrets.sh"
}
