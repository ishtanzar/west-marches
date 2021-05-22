terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
    }
  }

  backend "s3" {
    bucket = "westmarches-infra"
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
}
