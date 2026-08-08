# 手動跑一次,建立 Terraform remote state 用的 GCS bucket + 開通核心 API。
# state bucket 本身無法被自己管的 backend 儲存(雞生蛋問題),此目錄用 local state。
#
# 用法:
#   cd terraform/bootstrap
#   terraform init
#   terraform apply -var="project_id=<new-project-id>"
#
# 跑完後,把輸出的 bucket 名稱填進 ../backend.tf 的 -backend-config,
# 到 ../ 目錄 terraform init 接上 remote state。

terraform {
  required_version = ">= 1.7.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "新 GCP project id(已建立、空的)"
}

variable "region" {
  type    = string
  default = "asia-east1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "bootstrap_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
  ])
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}

resource "google_storage_bucket" "tfstate" {
  name                        = "${var.project_id}-tfstate"
  project                     = var.project_id
  location                    = "ASIA-EAST1"
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 10
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.bootstrap_apis]
}

output "tfstate_bucket" {
  value = google_storage_bucket.tfstate.name
}
