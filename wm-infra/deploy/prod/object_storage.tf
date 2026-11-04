resource "scaleway_object_bucket" "backups" {
  name = "westmarches-backups"
}

resource "scaleway_object_bucket" "data" {
  name = "westmarches-data"

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

# Bucket policies (2023-04-17) only grant access to explicitly allowed principals;
# Deny statements are ignored and groups are not supported, so the administrators
# group is expanded into its user and application IDs. Anyone not listed (Foundry
# included) has no access. The organization owner can always edit the policy.
data "scaleway_iam_group" "administrators" {
  name = var.administrators_group_name
}

locals {
  administrator_principals = concat(
    [for id in data.scaleway_iam_group.administrators.user_ids : "user_id:${id}"],
    [for id in data.scaleway_iam_group.administrators.application_ids : "application_id:${id}"],
  )
}

resource "scaleway_object_bucket_policy" "data" {
  bucket = scaleway_object_bucket.data.name
  policy = jsonencode({
    Version = "2023-04-17"
    Id      = "foundry-data"
    Statement = [
      {
        Sid    = "FoundryReadWrite"
        Effect = "Allow"
        Principal = { SCW = "application_id:${var.foundry_application_id}" }
        Action = ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = [
          scaleway_object_bucket.data.name,
          "${scaleway_object_bucket.data.name}/*",
        ]
      },
      {
        Sid    = "AdministratorsFullAccess"
        Effect = "Allow"
        Principal = { SCW = local.administrator_principals }
        Action = ["s3:*"]
        Resource = [
          scaleway_object_bucket.data.name,
          "${scaleway_object_bucket.data.name}/*",
        ]
      }
    ]
  })
}

resource "scaleway_object_bucket_policy" "backups" {
  bucket = scaleway_object_bucket.backups.name
  policy = jsonencode({
    Version = "2023-04-17"
    Id      = "westmarches-backups"
    Statement = [{
      Sid       = "AdministratorsFullAccess"
      Effect    = "Allow"
      Principal = { SCW = local.administrator_principals }
      Action    = ["s3:*"]
      Resource = [
        scaleway_object_bucket.backups.name,
        "${scaleway_object_bucket.backups.name}/*",
      ]
    }]
  })
}
