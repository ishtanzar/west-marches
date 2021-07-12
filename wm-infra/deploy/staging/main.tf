terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
    }
  }

  backend "s3" {
    bucket = "westmarches-test-infra"
    key    = "tfstate/main.tfstate"
    region = "fr-par"

    endpoint = "https://s3.fr-par.scw.cloud"
    skip_region_validation = true
    skip_credentials_validation = true
  }

  required_version = ">= 0.13"
}

variable "gandi_key" {}

module "main" {
  source = "../../modules/main"

  gandi_key = var.gandi_key
  host_name = "westmarchesdelacave-test"
  backup_bucket = "westmarches-infra-test-backups"
  ssh_key_id = "5cff6783-ee69-4366-9ffe-4bafb9340e4d"
}
