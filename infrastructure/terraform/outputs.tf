# DORA Compliance System - Terraform Outputs
# Output values from the main configuration

# Basic Infrastructure Outputs
output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = local.project
}

output "name_prefix" {
  description = "Common name prefix for resources"
  value       = local.name_prefix
}

# Network Infrastructure Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.aws_infrastructure.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.aws_infrastructure.vpc_cidr
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.aws_infrastructure.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.aws_infrastructure.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.aws_infrastructure.database_subnet_ids
}

output "availability_zones" {
  description = "Availability zones used"
  value       = local.availability_zones
}

# EKS Cluster Outputs
output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks_cluster.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks_cluster.cluster_endpoint
  sensitive   = false
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks_cluster.cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks_cluster.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks_cluster.cluster_version
}

output "node_groups" {
  description = "EKS node group configurations"
  value       = module.eks_cluster.node_groups
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider for IRSA"
  value       = module.eks_cluster.oidc_provider_arn
}

# Database Outputs
output "rds_cluster_endpoint" {
  description = "RDS cluster endpoint"
  value       = module.database_cluster.rds_cluster_endpoint
  sensitive   = false
}

output "rds_cluster_reader_endpoint" {
  description = "RDS cluster reader endpoint"
  value       = module.database_cluster.rds_cluster_reader_endpoint
  sensitive   = false
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.database_cluster.redis_endpoint
  sensitive   = false
}

output "documentdb_endpoint" {
  description = "DocumentDB cluster endpoint"
  value       = module.database_cluster.documentdb_endpoint
  sensitive   = false
}

output "database_security_group_id" {
  description = "Security group ID for database access"
  value       = module.database_cluster.security_group_id
}

# Security Outputs
output "kms_key_id" {
  description = "The ID of the KMS key"
  value       = aws_kms_key.main.id
}

output "kms_key_arn" {
  description = "The ARN of the KMS key"
  value       = aws_kms_key.main.arn
}

output "vault_load_balancer_dns" {
  description = "HashiCorp Vault load balancer DNS name"
  value       = module.security.vault_load_balancer_dns
  sensitive   = false
}

output "secrets_manager_arns" {
  description = "ARNs of AWS Secrets Manager secrets"
  value       = module.security.secrets_manager_arns
  sensitive   = true
}

# Monitoring Outputs
output "prometheus_endpoint" {
  description = "Amazon Managed Prometheus workspace endpoint"
  value       = module.monitoring.prometheus_endpoint
  sensitive   = false
}

output "grafana_endpoint" {
  description = "Amazon Managed Grafana workspace endpoint"
  value       = module.monitoring.grafana_endpoint
  sensitive   = false
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group ARNs"
  value       = module.monitoring.cloudwatch_log_groups
}

# Networking Outputs
output "load_balancer_dns_name" {
  description = "DNS name of the application load balancer"
  value       = module.networking.load_balancer_dns_name
  sensitive   = false
}

output "load_balancer_zone_id" {
  description = "Zone ID of the application load balancer"
  value       = module.networking.load_balancer_zone_id
}

output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = module.networking.certificate_arn
}

output "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  value       = module.networking.route53_zone_id
}

output "domain_name" {
  description = "Primary domain name"
  value       = local.domain_name
}

output "full_domain" {
  description = "Full domain name (subdomain.domain)"
  value       = local.full_domain
}

# Application Endpoints
output "api_endpoint" {
  description = "API endpoint URL"
  value       = "https://${local.full_domain}"
  sensitive   = false
}

output "dashboard_endpoint" {
  description = "Dashboard endpoint URL"
  value       = "https://dashboard.${local.domain_name}"
  sensitive   = false
}

# Utility Outputs for Automation
output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks_cluster.cluster_name}"
}

output "helm_values" {
  description = "Common Helm values for application deployments"
  value = {
    global = {
      environment = var.environment
      region      = var.aws_region
      domain      = local.domain_name
      cluster     = module.eks_cluster.cluster_name
    }
    database = {
      postgres = {
        host = module.database_cluster.rds_cluster_endpoint
        port = 5432
      }
      redis = {
        host = module.database_cluster.redis_endpoint
        port = 6379
      }
      mongodb = {
        host = module.database_cluster.documentdb_endpoint
        port = 27017
      }
    }
    monitoring = {
      prometheus = module.monitoring.prometheus_endpoint
      grafana    = module.monitoring.grafana_endpoint
    }
  }
  sensitive = false
}

# Cost Tracking Outputs
output "estimated_monthly_cost" {
  description = "Estimated monthly cost (rough calculation)"
  value = {
    eks_cluster     = "$150-300"
    rds_cluster     = "$200-400"
    elasticache     = "$100-200"
    documentdb      = "$150-300"
    load_balancers  = "$25-50"
    nat_gateways    = "$45-90"
    total_estimate  = "$670-1340"
    note           = "Actual costs depend on usage, data transfer, and instance utilization"
  }
}

# Security and Compliance Outputs
output "compliance_status" {
  description = "Compliance configuration status"
  value = {
    encryption_at_rest    = var.enable_encryption
    encryption_in_transit = true
    multi_az_deployment   = true
    backup_enabled        = true
    monitoring_enabled    = var.enable_monitoring
    access_logging        = true
    audit_logging         = true
    vpc_flow_logs         = true
  }
}

# Resource Tags
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# Connection Information
output "connection_info" {
  description = "Connection information for external tools"
  value = {
    cluster_name    = module.eks_cluster.cluster_name
    cluster_region  = var.aws_region
    vpc_id          = module.aws_infrastructure.vpc_id
    security_groups = {
      cluster  = module.eks_cluster.cluster_security_group_id
      database = module.database_cluster.security_group_id
    }
    subnets = {
      public   = module.aws_infrastructure.public_subnet_ids
      private  = module.aws_infrastructure.private_subnet_ids
      database = module.aws_infrastructure.database_subnet_ids
    }
  }
  sensitive = false
}

# Disaster Recovery Information
output "disaster_recovery" {
  description = "Disaster recovery configuration"
  value = {
    backup_retention_days = var.backup_retention_period
    cross_region_backup   = var.enable_cross_region_backup
    secondary_region      = var.secondary_region
    rds_snapshots         = "automatic"
    configuration_backup  = "git-based"
  }
} 