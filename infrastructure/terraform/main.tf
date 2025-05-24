# DORA Compliance System - Main Terraform Configuration
# This file orchestrates all infrastructure components

terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    # Backend configuration is provided via backend config files
    # See environments/{env}/backend.tfvars
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# Configure Kubernetes Provider
provider "kubernetes" {
  host                   = module.eks_cluster.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks_cluster.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = ["eks", "get-token", "--cluster-name", module.eks_cluster.cluster_name]
  }
}

# Configure Helm Provider
provider "helm" {
  kubernetes {
    host                   = module.eks_cluster.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks_cluster.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = ["eks", "get-token", "--cluster-name", module.eks_cluster.cluster_name]
    }
  }
}

# Local values for common configuration
locals {
  environment = var.environment
  project     = "dora-compliance"
  
  common_tags = {
    Project     = local.project
    Environment = local.environment
    ManagedBy   = "terraform"
    Repository  = "dora-compliance-system"
    Owner       = var.owner_email
    CostCenter  = var.cost_center
    Compliance  = "DORA"
  }
  
  # Naming convention: {project}-{environment}-{component}
  name_prefix = "${local.project}-${local.environment}"
  
  # Network configuration
  vpc_cidr = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names
  
  # Domain configuration
  domain_name = var.domain_name
  subdomain   = var.subdomain_prefix
  full_domain = "${local.subdomain}.${local.domain_name}"
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Random password for databases
resource "random_password" "master_password" {
  length  = 32
  special = true
}

# KMS key for encryption
resource "aws_kms_key" "main" {
  description             = "KMS key for ${local.name_prefix} encryption"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-kms-key"
  })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name_prefix}-main"
  target_key_id = aws_kms_key.main.key_id
}

# AWS Infrastructure Module
module "aws_infrastructure" {
  source = "./modules/aws-infrastructure"
  
  # Basic configuration
  project     = local.project
  environment = local.environment
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_cidr           = local.vpc_cidr
  availability_zones = local.availability_zones
  
  # Security configuration
  kms_key_id = aws_kms_key.main.arn
  
  # Tags
  tags = local.common_tags
}

# EKS Cluster Module
module "eks_cluster" {
  source = "./modules/eks-cluster"
  
  # Dependencies
  depends_on = [module.aws_infrastructure]
  
  # Basic configuration
  project     = local.project
  environment = local.environment
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id              = module.aws_infrastructure.vpc_id
  private_subnet_ids  = module.aws_infrastructure.private_subnet_ids
  
  # Security configuration
  kms_key_id = aws_kms_key.main.arn
  
  # Cluster configuration
  cluster_version = var.eks_cluster_version
  node_groups     = var.eks_node_groups
  
  # Tags
  tags = local.common_tags
}

# Database Cluster Module
module "database_cluster" {
  source = "./modules/database-cluster"
  
  # Dependencies
  depends_on = [module.aws_infrastructure]
  
  # Basic configuration
  project     = local.project
  environment = local.environment
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id             = module.aws_infrastructure.vpc_id
  private_subnet_ids = module.aws_infrastructure.private_subnet_ids
  
  # Security configuration
  kms_key_id = aws_kms_key.main.arn
  
  # Database configuration
  master_password = random_password.master_password.result
  
  # Tags
  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"
  
  # Dependencies
  depends_on = [module.aws_infrastructure, module.eks_cluster]
  
  # Basic configuration
  project     = local.project
  environment = local.environment
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id     = module.aws_infrastructure.vpc_id
  subnet_ids = module.aws_infrastructure.private_subnet_ids
  
  # Cluster configuration
  cluster_name = module.eks_cluster.cluster_name
  cluster_arn  = module.eks_cluster.cluster_arn
  
  # Security configuration
  kms_key_id = aws_kms_key.main.arn
  
  # Tags
  tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  # Dependencies
  depends_on = [module.aws_infrastructure, module.eks_cluster]
  
  # Basic configuration
  project     = local.project
  environment = local.environment
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id     = module.aws_infrastructure.vpc_id
  subnet_ids = module.aws_infrastructure.private_subnet_ids
  
  # Cluster configuration
  cluster_name = module.eks_cluster.cluster_name
  
  # Security configuration
  kms_key_id = aws_kms_key.main.arn
  
  # Tags
  tags = local.common_tags
}

# Networking Module
module "networking" {
  source = "./modules/networking"
  
  # Dependencies
  depends_on = [module.aws_infrastructure, module.eks_cluster]
  
  # Basic configuration
  project     = local.project
  environment = local.environment
  name_prefix = local.name_prefix
  
  # Network configuration
  vpc_id              = module.aws_infrastructure.vpc_id
  public_subnet_ids   = module.aws_infrastructure.public_subnet_ids
  private_subnet_ids  = module.aws_infrastructure.private_subnet_ids
  
  # Domain configuration
  domain_name = local.domain_name
  subdomain   = local.subdomain
  full_domain = local.full_domain
  
  # Cluster configuration
  cluster_name = module.eks_cluster.cluster_name
  
  # Security configuration
  kms_key_id = aws_kms_key.main.arn
  
  # Tags
  tags = local.common_tags
} 