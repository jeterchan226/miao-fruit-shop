resource "google_storage_bucket" "product_images" {
  project                     = var.project_id
  name                        = var.gcs_bucket_name
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  cors {
    origin          = ["*"] # 商品圖走 signed URL 上傳、public_url 直讀,同 backend/app/services/gcs_service.py
    method          = ["GET", "PUT"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.apis]
}

# public_url() 直接組 https://storage.googleapis.com/<bucket>/<blob>,物件需可公開讀。
resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.product_images.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# 簽 signed URL(gcs_service.py generate_signed_url)需要一把可簽章的 SA key,
# Cloud Run 預設 SA 沒有私鑰不能直接簽,故建獨立 SA + key。
# key 只在第一次 apply 產生,之後想換要 terraform taint 這個 resource。
resource "google_service_account" "gcs_signer" {
  project      = var.project_id
  account_id   = "miao-gcs-signer"
  display_name = "miao-fruit-shop GCS signed-URL 簽章帳號"
}

resource "google_storage_bucket_iam_member" "signer_object_admin" {
  bucket = google_storage_bucket.product_images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcs_signer.email}"
}

resource "google_service_account_key" "gcs_signer_key" {
  service_account_id = google_service_account.gcs_signer.name
}
