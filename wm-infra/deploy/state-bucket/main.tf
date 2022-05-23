terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "2.2.1"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "4.15.1"
    }

  }

  required_version = ">= 0.13"
}

provider "aws" {
  skip_region_validation      = true
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  region                      = "fr-par"

  endpoints {
    s3 = "https://s3.fr-par.scw.cloud"
  }
}

resource "scaleway_object_bucket" "main" {
  name     = "westmarches-infra"
  acl      = "private"
}

resource "aws_s3_bucket_policy" "main-policy" {
  bucket = scaleway_object_bucket.main.name
  policy = file("files/bucket-iac-policy.json")
}
