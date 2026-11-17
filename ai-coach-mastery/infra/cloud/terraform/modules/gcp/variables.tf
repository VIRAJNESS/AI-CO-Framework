# ============================================================================
# GCP module — provisioning contract (Step-1 skeleton).
# Maps the platform's neutral needs onto GCP services:
#   DB      -> Cloud SQL for PostgreSQL (pgvector supported)
#   Cache   -> Memorystore for Redis
#   Storage -> Cloud Storage (STORAGE_PROVIDER=gcs)
#   Cluster -> GKE
#   Registry-> Artifact Registry
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

variable "gcp_project_id" {
  description = "GCP project ID to deploy into."
  type        = string
}

variable "region" {
  description = "GCP region (e.g. europe-west1)."
  type        = string
}

variable "db_tier" {
  description = "Cloud SQL machine tier."
  type        = string
  default     = "db-f1-micro"
}

variable "redis_memory_gb" {
  description = "Memorystore Redis memory size in GB."
  type        = number
  default     = 1
}

variable "gke_node_count" {
  description = "Default GKE node pool size."
  type        = number
  default     = 2
}

variable "labels" {
  description = "Common resource labels."
  type        = map(string)
  default     = {}
}
