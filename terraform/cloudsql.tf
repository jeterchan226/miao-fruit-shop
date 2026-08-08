resource "random_password" "db_password" {
  length  = 32
  special = false # asyncpg URL 組字串會 quote_plus,純英數字避免多餘困擾
}

resource "google_sql_database_instance" "main" {
  project             = var.project_id
  name                = var.sql_instance_name
  region              = var.region
  database_version    = "POSTGRES_17" # 對齊 backend/docker-compose.yml
  deletion_protection = var.sql_deletion_protection

  settings {
    edition = "ENTERPRISE" # db-f1-micro 等共享核心規格只有 Enterprise edition 支援;
    # 新 project 預設 Enterprise Plus,不明確指定會噴 "Invalid Tier for ENTERPRISE_PLUS Edition"
    tier              = var.sql_tier
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled = true # Cloud Run 走內建 Cloud SQL Auth Proxy,不吃公開網路路徑
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "main" {
  project  = var.project_id
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  project  = var.project_id
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}
