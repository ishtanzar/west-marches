terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "2.89.0"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "5.70.0"
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
  name = "westmarches-infra"

  lifecycle {
    prevent_destroy = true
  }

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "purge-noncurrent-versions"
    enabled = true

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  lifecycle_rule {
    id                                     = "abort-incomplete-multipart-uploads"
    enabled                                = true
    abort_incomplete_multipart_upload_days = 7
  }
}

resource "scaleway_object_bucket_acl" "main" {
  bucket = scaleway_object_bucket.main.name
  acl    = "private"
}

variable "prod_application_id" {
  description = "Scaleway IAM application ID for prod (tfstate/prod)"
  type        = string
  default     = "c681208e-0ea6-4bbb-8243-a4591156fa1f"
}

variable "test_application_id" {
  description = "Scaleway IAM application ID for test (tfstate/test)"
  type        = string
  default     = "deac23e7-5d54-4a7b-b1da-963fee74af11"
}

variable "admin_user_id" {
  description = "Scaleway IAM user ID with full admin access to the bucket"
  type        = string
  default     = "04ae4583-f482-400c-b730-f34578562736"
}

resource "scaleway_object_bucket_policy" "main" {
  bucket = scaleway_object_bucket.main.name

  policy = jsonencode({
    Version = "2023-04-17"
    Id      = "westmarches-infra"
    Statement = [
      {
        Sid    = "AdminFullAccess"
        Effect = "Allow"
        Principal = {
          SCW = [
            "user_id:${var.admin_user_id}",
            "application_id:${var.prod_application_id}",
          ]
        }
        Action = ["s3:*"]
        Resource = [
          scaleway_object_bucket.main.name,
          "${scaleway_object_bucket.main.name}/*",
        ]
      },
      {
        Sid       = "TestListPrefix"
        Effect    = "Allow"
        Principal = { SCW = "application_id:${var.test_application_id}" }
        Action    = ["s3:ListBucket"]
        Resource  = scaleway_object_bucket.main.name
        Condition = {
          StringLike = { "s3:prefix" = ["tfstate/test", "tfstate/test/*"] }
        }
      },
      {
        Sid       = "TestReadWriteObjects"
        Effect    = "Allow"
        Principal = { SCW = "application_id:${var.test_application_id}" }
        Action    = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource  = "${scaleway_object_bucket.main.name}/tfstate/test/*"
      },
    ]
  })
}
