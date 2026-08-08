# Partial backend config — bucket 名稱不放這裡(避免硬編新舊 project 名稱),
# init 時用 -backend-config 帶入:
#
#   terraform init -backend-config="bucket=<project_id>-tfstate"
#
# bucket 由 terraform/bootstrap 建立。

terraform {
  backend "gcs" {
    prefix = "miao-fruit-shop/prod"
  }
}
