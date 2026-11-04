resource "scaleway_registry_namespace" "foundry" {
  name       = "westmarches-prod"
  project_id = var.scaleway_project_id
  region     = var.scaleway_region
  is_public  = false

  lifecycle {
    prevent_destroy = true
  }
}
