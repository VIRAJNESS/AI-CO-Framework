# Outputs form the contract the Helm deployment consumes (DB_URL, REDIS_URL,
# storage settings). Values become real once Step-2 resources are implemented.

output "resource_group_name" {
  description = "Name of the anchor resource group."
  value       = azurerm_resource_group.main.name
}

output "db_url" {
  description = "JDBC/SQLAlchemy-compatible Postgres URL (set in step-2)."
  value       = null
}

output "redis_url" {
  description = "Redis connection URL (set in step-2)."
  value       = null
}

output "storage_account_endpoint" {
  description = "Blob endpoint for STORAGE_PROVIDER=azure_blob (set in step-2)."
  value       = null
}

output "registry_login_server" {
  description = "ACR login server for image pushes (set in step-2)."
  value       = null
}

output "kube_config_host" {
  description = "AKS API endpoint (set in step-2)."
  value       = null
}
