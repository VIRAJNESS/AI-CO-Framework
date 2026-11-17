# ============================================================================
# Azure module — Step-1 skeleton.
# Declares the provider requirement and resource-group anchor. Managed
# services (PostgreSQL Flexible Server, Azure Cache for Redis, Blob Storage,
# AKS, ACR) are intentionally left as documented TODO blocks: the module's
# interface (variables/outputs) is the contract later steps implement.
# ============================================================================

terraform {
  required_version = ">= 1.7"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = var.tags
}

# TODO(step-2): azurerm_postgresql_flexible_server  (enable pgvector extension)
# TODO(step-2): azurerm_redis_cache
# TODO(step-2): azurerm_storage_account + container (STORAGE_PROVIDER=azure_blob)
# TODO(step-2): azurerm_kubernetes_cluster (AKS) — node_count = var.aks_node_count
# TODO(step-2): azurerm_container_registry (ACR)
