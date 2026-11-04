# Kubernetes provider configuration
# Reads the existing kubeconfig from Scaleway Secret Manager

data "scaleway_secret" "k8s_admin" {
  name       = "admin"
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  path       = "/project/lesaventuriersducairn/prod/roles/k8s"
}

data "scaleway_secret" "kubelet_pull" {
  name       = "kubelet-pull"
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  path       = "/project/westmarches/prod"
}

data "scaleway_secret_version" "k8s_admin_current" {
  secret_id  = data.scaleway_secret.k8s_admin.id
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  revision   = "latest"
}

data "scaleway_secret_version" "kubelet_pull_current" {
  secret_id  = data.scaleway_secret.kubelet_pull.id
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  revision   = "latest"
}

# Decode the kubeconfig from the secret payload
# The secret might be stored as base64 or raw YAML
locals {
  k8s_namespace      = "lesaventuriersducairn-prod"
  k8s_kubeconfig_raw = data.scaleway_secret_version.k8s_admin_current.data
  # Try to decode if it's base64-encoded
  k8s_kubeconfig_decoded = can(base64decode(local.k8s_kubeconfig_raw)) ? base64decode(local.k8s_kubeconfig_raw) : local.k8s_kubeconfig_raw
  k8s_kubeconfig_yaml    = yamldecode(local.k8s_kubeconfig_decoded)
  kubelet_pull_credentials = jsondecode(base64decode(data.scaleway_secret_version.kubelet_pull_current.data))
}

provider "kubernetes" {
  config_path = null

  # Parse the kubeconfig stored in Secret Manager
  client_certificate     = try(base64decode(local.k8s_kubeconfig_yaml.users[0].user.client-certificate-data), null)
  client_key             = try(base64decode(local.k8s_kubeconfig_yaml.users[0].user.client-key-data), null)
  cluster_ca_certificate = try(base64decode(local.k8s_kubeconfig_yaml.clusters[0].cluster.certificate-authority-data), null)
  host                   = try(local.k8s_kubeconfig_yaml.clusters[0].cluster.server, null)
  token                  = try(local.k8s_kubeconfig_yaml.users[0].user.token, null)
}

# Optional: Add helm provider if needed for future deployments
# provider "helm" {
#   kubernetes {
#     client_certificate     = try(base64decode(local.k8s_kubeconfig_yaml.users[0].user.client-certificate-data), null)
#     client_key             = try(base64decode(local.k8s_kubeconfig_yaml.users[0].user.client-key-data), null)
#     cluster_ca_certificate = try(base64decode(local.k8s_kubeconfig_yaml.clusters[0].cluster.certificate-authority-data), null)
#     host                   = try(local.k8s_kubeconfig_yaml.clusters[0].cluster.server, null)
#     token                  = try(local.k8s_kubeconfig_yaml.users[0].user.token, null)
#   }
# }

provider "kustomization" {
  kubeconfig_raw = local.k8s_kubeconfig_decoded
}

data "kubernetes_service_account" "lesaventuriersducairn_admin" {
  metadata {
    name      = "lesaventuriersducairn-admin"
    namespace = local.k8s_namespace
  }
  depends_on = [null_resource.validate_provider]
}

# Dummy resource to force provider validation
resource "null_resource" "validate_provider" {
  provisioner "local-exec" {
    command = "echo 'Kubernetes provider configured'"
  }
}

resource "kubernetes_secret" "westmarches_registry" {
  metadata {
    name      = "westmarches-registry"
    namespace = local.k8s_namespace
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "rg.fr-par.scw.cloud" = {
          auth = base64encode("nologin:${local.kubelet_pull_credentials.secret_key}")
        }
      }
    })
  }

  depends_on = [data.kubernetes_service_account.lesaventuriersducairn_admin]
}
