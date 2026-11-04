
data "scaleway_secret" "foundry_data" {
  name       = "foundry"
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  path       = "/project/westmarches/prod"
}

data "scaleway_secret_version" "foundry_data_current" {
  secret_id  = data.scaleway_secret.foundry_data.id
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  revision   = "latest"
}

locals {
  # Payload: {"access_key": ..., "secret_key": ...}
  foundry_data_credentials = jsondecode(base64decode(data.scaleway_secret_version.foundry_data_current.data))
}

# Generate random password for Foundry admin key
resource "random_password" "foundry_admin_key" {
  length  = 32
  special = true
}

# Kubernetes Secret for Foundry credentials (injected as env vars)
resource "kubernetes_secret" "foundry_secrets" {
  metadata {
    name      = "foundry-secrets"
    namespace = local.k8s_namespace
  }

  data = {
    FOUNDRY_ADMIN_KEY   = random_password.foundry_admin_key.result
    FOUNDRY_LICENSE_KEY = trimspace(var.foundry_license_key)
  }

  type = "Opaque"

  depends_on = [data.kubernetes_service_account.lesaventuriersducairn_admin]
}

# Kubernetes Secret for Foundry S3 config (mounted as file)
resource "kubernetes_secret" "foundry_s3_config" {
  metadata {
    name      = "foundry-s3-config"
    namespace = local.k8s_namespace
  }

  data = {
    "s3config.json" = jsonencode({
      buckets  = [scaleway_object_bucket.data.name]
      region   = var.scaleway_region
      endpoint = "https://s3.${var.scaleway_region}.scw.cloud"
      credentials = {
        accessKeyId     = local.foundry_data_credentials.access_key
        secretAccessKey = local.foundry_data_credentials.secret_key
      }
    })
  }

  type = "Opaque"

  depends_on = [data.kubernetes_service_account.lesaventuriersducairn_admin]
}
