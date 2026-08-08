variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type    = string
  default = "asia-east1"
}

# --- 命名沿用現有正式環境,deploy.sh / docs 不用改 ---
variable "service_name" {
  type    = string
  default = "miao-api"
}

variable "migrate_job_name" {
  type    = string
  default = "miao-api-migrate"
}

variable "sql_instance_name" {
  type    = string
  default = "miao-fruit-shop-db"
}

variable "db_name" {
  type    = string
  default = "miao_fruit_shop"
}

variable "db_user" {
  type    = string
  default = "miao_app"
}

# GCS bucket 名稱全 GCP 域唯一(跨 project),換新 project 通常不能沿用舊名。
variable "gcs_bucket_name" {
  type        = string
  description = "商品圖片 bucket 名稱(需全域唯一,建議 <project_id>-images)"
}

variable "sql_tier" {
  type    = string
  default = "db-f1-micro"
}

variable "sql_deletion_protection" {
  type    = bool
  default = true
}

# --- CORS ---
variable "cors_origins" {
  type        = string
  description = "逗號分隔白名單,結尾不可帶 /(見 CLAUDE.md CORS 說明)"
  default     = "http://localhost:8080"
}

variable "cors_origin_regex" {
  type    = string
  default = "https://frontend(-[a-z0-9]+)*-jeterchans-projects\\.vercel\\.app"
}

# --- LINE(Messaging API channel;LIFF ID 同前端 VITE_MIAO_LIFF_ID)---
# 值不進 tfvars/state:Terraform 只建立空 Secret 容器,
# 實際 token/secret 用 gcloud secrets versions add 手動灌,換帳號時比照辦理。
variable "line_liff_id" {
  type    = string
  default = ""
}
