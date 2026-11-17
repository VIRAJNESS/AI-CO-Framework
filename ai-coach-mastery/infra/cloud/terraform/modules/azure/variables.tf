# ============================================================================
# Azure module — provisioning contract (Step-1 skeleton).
# Maps the platform's neutral needs onto Azure services:
#   DB      -> Azure Database for PostgreSQL Flexible Server (pgvector capable)
#   Cache   -> Azure Cache for Redis
#   Storage -> Azure Blob Storage (STORAGE_PROVIDER=azure_blob)
#   Cluster -> AKS
#   Registry-> ACR
# ============================================================================

variable "project_name" {
  description = "Project slug used to name all resources."
  type        = string
  default     = "ai-coach-mastery"
}

variable "environment" {
  description = "Deployment environment (dev|staging|prod)."
  type        = string
}

variable "location" {
  description = "Azure region (e.g. westeurope)."
  type        = string
}

variable "postgres_sku" {
  description = "SKU for PostgreSQL Flexible Server."
  type        = string
  default     = "B_Standard_B1ms"
}

variable "redis_sku" {
  description = "SKU for Azure Cache for Redis."
  type        = string
  default     = "Basic"
}

variable "aks_node_count" {
  description = "Default AKS node pool size."
  type        = number
  default     = 2
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}
