resource "random_password" "filestash_admin_password" {
  length  = 32
  special = true
}

resource "random_password" "filestash_secret_key" {
  length  = 16
  special = false
}

locals {
  filestash_config = {
    general = {
      host       = "filestash.lesaventuriersducairn.fr"
      secret_key = random_password.filestash_secret_key.result
    }
    features = {
      share = {
        enable = false
      }
      protection = {
        enable_chromecast = false
      }
      collaborative = {
        enable = false
      }
      video = {
        enable_transcoder = false
      }
    }
    connections = [{
      type  = "s3"
      label = "Foundry data"
    }]
    middleware = {
      identity_provider = {
        type = "passthrough"
        params = jsonencode({
          strategy = "username_and_password"
        })
      }
      attribute_mapping = {
        related_backend = "Foundry data"
        params = jsonencode({
          "Foundry data" = {
            type              = "s3"
            region            = var.scaleway_region
            endpoint          = "https://s3.${var.scaleway_region}.scw.cloud"
            path              = "/${scaleway_object_bucket.data.name}/"
            access_key_id     = "{{ .user }}"
            secret_access_key = "{{ .password }}"
          }
        })
      }
    }
  }
}

resource "kubernetes_secret" "filestash_secrets" {
  metadata {
    name      = "filestash-secrets"
    namespace = local.k8s_namespace
  }

  data = {
    ADMIN_PASSWD  = random_password.filestash_admin_password.bcrypt_hash
    "config.json" = jsonencode(local.filestash_config)
  }

  type = "Opaque"

  depends_on = [data.kubernetes_service_account.lesaventuriersducairn_admin]
}
