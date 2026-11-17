terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "2.89.0"
    }
  }

  backend "s3" {
    bucket = "westmarches-infra"
    key    = "tfstate/test/main.tfstate"
    region = "fr-par"

    endpoint                    = "https://s3.fr-par.scw.cloud"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
  }

  required_version = ">= 1.5"
}

provider "scaleway" {
  organization_id = var.scaleway_organization_id
  project_id      = var.scaleway_project_id
  region          = var.scaleway_region
}
