# Contract outputs consumed by the Helm deployment pipeline.

output "artifacts_bucket" {
  description = "S3 bucket name for artifact storage (STORAGE_PROVIDER=s3)."
  value       = aws_s3_bucket.artifacts.bucket
}

output "db_url" {
  description = "Postgres connection URL (set in step-2 with RDS)."
  value       = null
}

output "redis_url" {
  description = "Redis connection URL (set in step-2 with ElastiCache)."
  value       = null
}

output "registry_url" {
  description = "ECR registry URL (set in step-2)."
  value       = null
}

output "eks_cluster_endpoint" {
  description = "EKS API endpoint (set in step-2)."
  value       = null
}
