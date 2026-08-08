locals {
  cloudsql_connection_name = google_sql_database_instance.main.connection_name
  db_host                  = "/cloudsql/${local.cloudsql_connection_name}"

  # service 與 job 共用的 DB / secret 環境變數(容器啟動指令不同,env 相同)
  common_env = [
    { name = "DB_USER", value = var.db_user },
    { name = "DB_NAME", value = var.db_name },
    { name = "DB_HOST", value = local.db_host },
  ]
}

# --- API service ---
resource "google_cloud_run_v2_service" "api" {
  project             = var.project_id
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false # 單人低頻專案,不擋 terraform 內的 replace(provider 預設 true)

  template {
    service_account = google_service_account.run_runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [local.cloudsql_connection_name]
      }
    }

    containers {
      # placeholder;實際部署由 backend/deploy.sh 的 gcloud run deploy --source 覆蓋,
      # Terraform 不管 image(見下方 lifecycle.ignore_changes)。
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }
      env {
        name  = "CORS_ORIGIN_REGEX"
        value = var.cors_origin_regex
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.product_images.name
      }
      env {
        name  = "LINE_LIFF_ID"
        value = var.line_liff_id
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GCS_CREDENTIALS_B64"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gcs_credentials_b64.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "LINE_CHANNEL_ACCESS_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.line_channel_access_token.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "LINE_CHANNEL_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.line_channel_secret.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.db_password,
    google_secret_manager_secret_version.jwt_secret,
    google_secret_manager_secret_version.line_channel_access_token_placeholder,
    google_secret_manager_secret_version.line_channel_secret_placeholder,
  ]
}

# --- migration job(alembic upgrade head,idempotent)---
resource "google_cloud_run_v2_job" "migrate" {
  project  = var.project_id
  name     = var.migrate_job_name
  location = var.region

  template {
    template {
      service_account = google_service_account.run_runtime.email
      max_retries     = 1

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [local.cloudsql_connection_name]
        }
      }

      containers {
        image   = "us-docker.pkg.dev/cloudrun/container/hello" # deploy.sh 會 update --image 到最新 build
        command = ["uv"]
        args    = ["run", "--no-dev", "alembic", "upgrade", "head"]

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }

        dynamic "env" {
          for_each = local.common_env
          content {
            name  = env.value.name
            value = env.value.value
          }
        }

        env {
          name = "DB_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "latest"
            }
          }
        }
        env {
          # config.py 的 Settings.jwt_secret 是必填欄位,alembic env.py 會 import app.core.config,
          # 沒設這個 job 在 import 階段就 pydantic ValidationError,連 DB 都連不到。
          name = "JWT_SECRET"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.jwt_secret.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_version.db_password,
    google_secret_manager_secret_version.jwt_secret,
  ]
}
