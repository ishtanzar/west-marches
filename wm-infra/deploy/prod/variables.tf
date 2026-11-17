
variable "gandi_key" {}

variable "discord_bot_secret" {
  type      = string
  sensitive = true
}

variable "discord_owner_id" {
  type = string
}

variable "discord_api_token" {
  type      = string
  sensitive = true
}

variable "kanka_token" {
  type      = string
  sensitive = true
}

variable "discord_aws_access_key_id" {
  type      = string
  sensitive = true
}

variable "discord_aws_secret_key" {
  type      = string
  sensitive = true
}

variable "discord_aws_region" {
  type = string
}

variable "FOUNDRY_HOSTNAME" {
  default = "westmarchesdelacave"
}

variable "scaleway_project_id" {
  description = "Scaleway project ID for Secret Manager"
  type        = string
  default     = "395a81f2-0abe-417b-9e08-95079a607e2f"
}

variable "scaleway_region" {
  description = "Scaleway region"
  type        = string
  default     = "fr-par"
}

variable "foundry_license_key" {
  description = "Purchased Foundry VTT license key supplied at runtime"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.foundry_license_key)) >= 24
    error_message = "Supply a valid Foundry license key through FOUNDRY_LICENSE_KEY in the prod environment."
  }
}

variable "administrators_group_name" {
  description = "IAM group whose users and applications keep full access to policy-protected buckets"
  type        = string
  default     = "Westmarches Administrators"
}

variable "iac_application_id" {
  description = "IAM application ID of westmarches-iac, which keeps full access to policy-protected buckets"
  type        = string
  default     = "c681208e-0ea6-4bbb-8243-a4591156fa1f"
}

variable "scaleway_organization_id" {
  description = "Fixed Scaleway Organization for the management API"
  type        = string
  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.scaleway_organization_id))
    error_message = "Supply the management API Organization UUID."
  }
}

variable "s3_editors_group_id" {
  description = "Fixed, existing editors IAM group for the management API"
  type        = string
  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.s3_editors_group_id))
    error_message = "Supply the editors group UUID."
  }
}

variable "s3_gm_guild_id" {
  description = "Fixed Discord GM guild snowflake, also used by the bot config"
  type        = string
  validation {
    condition     = can(regex("^[1-9][0-9]{0,19}$", var.s3_gm_guild_id))
    error_message = "Supply the Discord GM guild snowflake."
  }
}

variable "s3_discord_bot_id" {
  description = "Fixed Discord bot snowflake; verified against the token on startup"
  type        = string
  validation {
    condition     = can(regex("^[1-9][0-9]{0,19}$", var.s3_discord_bot_id))
    error_message = "Supply the Discord bot snowflake."
  }
}

variable "management_api_database_host" {
  type        = string
  description = "External MySQL host used by the management API."
}

variable "management_api_database_port" {
  type    = number
  default = 3306
}

variable "management_api_database_name" {
  type    = string
  default = "westmarches"
}
