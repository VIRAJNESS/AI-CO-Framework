# ============================================================================
# GCP module — Step-1 skeleton.
# Declares provider requirement and the artifacts GCS bucket anchor. Remaining
# managed services are documented TODOs; variables/outputs are the contract.
# ============================================================================

terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Artifact storage — maps 1:1 to the local MinIO bucket; the ai-engine's gcs
# adapter (step-2) consumes it via STORAGE_PROVIDER=gcs.
resource "google_storage_bucket" "artifacts" {
  name                        = "${local.name_prefix}-artifacts"
  project                     = var.gcp_project_id
  location                    = var.region
  uniform_bucket_level_access = true
  labels                      = var.labels
}

# TODO(step-2): google_sql_database_instance (PostgreSQL 16, pgvector flag)
# TODO(step-2): google_redis_instance (Memorystore, memory = var.redis_memory_gb)
# TODO(step-2): google_container_cluster (GKE) + node pool (var.gke_node_count)
# TODO(step-2): google_artifact_registry_repository (docker format)
