# ============================================================================
# AWS module — Step-1 skeleton.
# Declares provider requirement and the artifact S3 bucket anchor. Remaining
# managed services are documented TODOs; variables/outputs are the contract.
# ============================================================================

terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Artifact storage — the one concrete resource: it maps 1:1 to the local MinIO
# bucket and lets STORAGE_PROVIDER=s3 work unchanged in AWS.
resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name_prefix}-artifacts"
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# TODO(step-2): aws_db_instance (RDS PostgreSQL 16, pgvector via CREATE EXTENSION)
# TODO(step-2): aws_elasticache_cluster (Redis 7)
# TODO(step-2): aws_eks_cluster + managed node group (size = var.eks_node_count)
# TODO(step-2): aws_ecr_repository per service (frontend, core-api, ai-engine)
