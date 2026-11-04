
variable "gandi_key" {}

variable "scw_ssh_key_id" {}

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

variable "foundry_application_id" {
  description = "IAM application ID used by Foundry to access Object Storage"
  type        = string
  default     = "3475973f-345c-494f-b322-04add2eed803"
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
