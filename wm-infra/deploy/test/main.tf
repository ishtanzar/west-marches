terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
    }
  }

  backend "s3" {
    bucket = "westmarches-test-iac"
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
  backup_bucket = "westmarches-test-backups"
  ssh_key_id = "b58acf4e-c85b-4087-b2f1-9578418a5f9c"
}
