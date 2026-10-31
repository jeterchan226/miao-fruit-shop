terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~>8.9"
    }
  }

  backend "gcs" {
    bucket = "miao-fruit-shop-dev-v01-tfstate"
    prefix = "dev"
  }
}