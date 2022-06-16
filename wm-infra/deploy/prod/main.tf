terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "2.1.0"
    }
  }

  backend "s3" {
    bucket = "westmarches-infra"
    key    = "tfstate/prod/main.tfstate"
    region = "fr-par"

    endpoint = "https://s3.fr-par.scw.cloud"
    skip_region_validation = true
    skip_credentials_validation = true
  }

  required_version = ">= 0.13"
}

variable "gandi_key" {}

variable scw_ssh_key_id {}

module "main" {
  source = "../../modules/main"

  gandi_key = var.gandi_key
  ssh_key_id = var.scw_ssh_key_id
  instance_type = "DEV1-M"
}
