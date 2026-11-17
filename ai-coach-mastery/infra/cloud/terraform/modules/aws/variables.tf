# ============================================================================
# AWS module — provisioning contract (Step-1 skeleton).
# Maps the platform's neutral needs onto AWS services:
#   DB      -> RDS for PostgreSQL (pgvector supported on PG 15+)
#   Cache   -> ElastiCache for Redis
#   Storage -> S3 (STORAGE_PROVIDER=s3)
#   Cluster -> EKS
#   Registry-> ECR
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

variable "region" {
  description = "AWS region (e.g. eu-west-1)."
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "redis_node_type" {
  description = "ElastiCache node type."
  type        = string
  default     = "cache.t4g.micro"
}

variable "eks_node_count" {
  description = "Default EKS managed node group size."
  type        = number
  default     = 2
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}
