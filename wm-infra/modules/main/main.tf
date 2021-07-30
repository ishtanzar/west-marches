terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
      version = "2.1.0"
    }

    restapi = {
      source = "fmontezuma/restapi"
      version = "1.14.1"
    }

    null = {
      source = "hashicorp/null"
      version = "3.1.0"
    }
  }
}

variable "gandi_key" {}

variable "host_name" {
  default = "westmarchesdelacave"
}

variable "backup_bucket" {
  default = "westmarches-infra-backups"
}

variable "ssh_key_id" {
  default = "def22f15-3be9-4fbc-ae46-49de416bd66a"
}

variable "instance_type" {
  default = "DEV1-S"
}

provider "restapi" {
  uri = "https://api.gandi.net/v5/livedns"
  id_attribute = "rrset_name"
  headers = {
    Authorization = "Apikey ${var.gandi_key}"
  }
}

data "scaleway_account_ssh_key" "ssh" {
  ssh_key_id = var.ssh_key_id
}

resource "scaleway_instance_ip" "public_ip" {}

resource "scaleway_instance_volume" "data" {
  type = "b_ssd"
  size_in_gb = 20
}

resource "scaleway_instance_security_group" "front" {
  inbound_default_policy = "drop"
  outbound_default_policy = "accept"

  inbound_rule {
    action = "accept"
    port = "22"
  }

  inbound_rule {
    action = "accept"
    port = "80"
  }

  inbound_rule {
    action = "accept"
    port = "443"
  }

  inbound_rule {
    action = "accept"
    port = "30000"
  }
}

resource "scaleway_instance_server" "main" {
  type = var.instance_type
  image = "ubuntu_focal"
  ip_id = scaleway_instance_ip.public_ip.id
  tags = ["foundry", "kanka"]
  additional_volume_ids = [scaleway_instance_volume.data.id]
  security_group_id = scaleway_instance_security_group.front.id
}

resource "scaleway_object_bucket" "backups" {
  name = var.backup_bucket
}

resource "null_resource" "ansible" {
  depends_on = [
    scaleway_instance_server.main,
  ]

  triggers = {
    timestamp = timestamp()
  }

  provisioner "local-exec" {
    command = "ansible-playbook -i inventory deploy.yml"
    working_dir = "${path.module}/ansible"

    environment = {
      ANSIBLE_FORCE_COLOR="1"
      SCW_VOLUME_ID=element(split("/", scaleway_instance_volume.data.id), 1)
      BACKUP_S3_BUCKET=var.backup_bucket
      FOUNDRY_HOSTNAME=var.host_name
    }
  }
}

resource "restapi_object" "dns_record" {
  path = "/domains/ishtanzar.net/records"
  read_path = "/domains/ishtanzar.net/records/{id}/A"
  data = jsonencode({
    rrset_name = var.host_name
    rrset_type = "A"
    rrset_values = [scaleway_instance_ip.public_ip.address]
    rrset_ttl = 300
  })
}

