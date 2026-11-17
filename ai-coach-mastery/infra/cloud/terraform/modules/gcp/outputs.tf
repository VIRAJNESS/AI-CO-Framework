# Contract outputs consumed by the Helm deployment pipeline.

output "artifacts_bucket" {
  description = "GCS bucket for artifact storage (STORAGE_PROVIDER=gcs)."
  value       = google_storage_bucket.artifacts.name
}

output "db_url" {
  description = "Postgres connection URL (set in step-2 with Cloud SQL)."
  value       = null
}

output "redis_url" {
  description = "Redis connection URL (set in step-2 with Memorystore)."
  value       = null
}

output "registry_url" {
  description = "Artifact Registry URL (set in step-2)."
  value       = null
}

output "gke_cluster_endpoint" {
  description = "GKE API endpoint (set in step-2)."
  value       = null
}
