terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
    }
    restapi = {
      source = "fmontezuma/restapi"
    }
  }
}

variable "gandi_key" {}

provider "restapi" {
  uri = "https://api.gandi.net/v5/livedns"
  id_attribute = "rrset_name"
  headers = {
    Authorization = "Apikey ${var.gandi_key}"
  }
}

data "scaleway_account_ssh_key" "ssh" {
  ssh_key_id = "5cff6783-ee69-4366-9ffe-4bafb9340e4d"
}

resource "scaleway_instance_ip" "public_ip" {}

resource "scaleway_instance_server" "main" {
  type = "DEV1-S"
  image = "ubuntu_focal"
  ip_id = scaleway_instance_ip.public_ip.id
  tags = ["foundry", "kanka"]

  provisioner "local-exec" {
    command = "ansible-playbook -i inventory deploy.yml"
    working_dir = "${path.module}/ansible"
  }
}

resource "restapi_object" "dns_record" {
  path = "/domains/ishtanzar.net/records"
  data = ""
}

