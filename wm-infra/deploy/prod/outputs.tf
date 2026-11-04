
output "foundry_admin_key" {
  description = "Generated Foundry admin key"
  value       = random_password.foundry_admin_key.result
  sensitive   = true
}

output "filestash_admin_password" {
  description = "Generated Filestash admin password"
  value       = random_password.filestash_admin_password.result
  sensitive   = true
}
