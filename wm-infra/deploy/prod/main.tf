terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "2.47.0"
    }
  }

  backend "s3" {
    bucket = "westmarches-infra"
    key    = "tfstate/prod/main.tfstate"
    region = "fr-par"

    endpoint = "https://s3.fr-par.scw.cloud"
    skip_region_validation = true
    skip_credentials_validation = true
    skip_metadata_api_check = true

#    Terraform 1.6+ only
#    skip_requesting_account_id = true
#    endpoints = {
#      s3 = "https://s3.fr-par.scw.cloud"
#    }
  }

  required_version = ">= 0.13"
}

variable "gandi_key" {}

variable scw_ssh_key_id {}

variable "FOUNDRY_HOSTNAME" {
  default = "westmarchesdelacave"
}

module "main" {
  source = "../../modules/main"

  gandi_key = var.gandi_key
  ssh_key_id = var.scw_ssh_key_id
  instance_type = "DEV1-M"
  host_name = var.FOUNDRY_HOSTNAME
}
