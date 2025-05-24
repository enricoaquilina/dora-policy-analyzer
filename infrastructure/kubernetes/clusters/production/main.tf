terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "s3" {
    bucket = "dora-terraform-state"
    key    = "kubernetes/production/terraform.tfstate"
    region = "eu-west-1"
    encrypt = true
    dynamodb_table = "dora-terraform-locks"
  }
}

# Variables
variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "dora-compliance-prod"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "kubernetes_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.28"
}

# Provider configuration
provider "aws" {
  region = var.region
  
  default_tags {
    tags = {
      Environment = "production"
      Project     = "dora-compliance"
      ManagedBy   = "terraform"
    }
  }
}

# Data sources for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module for EKS
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr
  
  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  database_subnets = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
  
  enable_nat_gateway   = true
  single_nat_gateway   = false  # HA setup with NAT gateway per AZ
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  # Tags required for EKS
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = 1
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = 1
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  
  tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# EKS Module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Control plane logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  
  # Encryption
  kms_key_enable_default_policy = true
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }
  
  # Cluster access
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]  # Restrict in production
  
  # Add-ons
  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["m5.large"]
    
    # Security
    enable_monitoring = true
    
    block_device_mappings = {
      xvda = {
        device_name = "/dev/xvda"
        ebs = {
          volume_size           = 100
          volume_type           = "gp3"
          encrypted             = true
          delete_on_termination = true
        }
      }
    }
    
    metadata_options = {
      http_endpoint               = "enabled"
      http_tokens                 = "required"
      http_put_response_hop_limit = 2
    }
  }
  
  # Node groups
  eks_managed_node_groups = {
    # System node group
    system = {
      name            = "system-node-group"
      use_name_prefix = false
      
      min_size     = 2
      max_size     = 4
      desired_size = 3
      
      instance_types = ["m5.large"]
      capacity_type  = "ON_DEMAND"
      
      labels = {
        role = "system"
      }
      
      taints = []
      
      tags = {
        NodeGroup = "system"
      }
    }
    
    # Agent node group
    agents = {
      name            = "agent-node-group"
      use_name_prefix = false
      
      min_size     = 3
      max_size     = 50
      desired_size = 10
      
      instance_types = ["m5.2xlarge", "m5.4xlarge"]
      capacity_type  = "SPOT"
      
      labels = {
        role = "agents"
        workload = "ai-ml"
      }
      
      taints = [{
        key    = "agents"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      
      tags = {
        NodeGroup = "agents"
      }
    }
    
    # Data node group
    data = {
      name            = "data-node-group"
      use_name_prefix = false
      
      min_size     = 3
      max_size     = 9
      desired_size = 6
      
      instance_types = ["r5.2xlarge"]
      capacity_type  = "ON_DEMAND"
      
      labels = {
        role = "data"
        storage = "high-iops"
      }
      
      taints = [{
        key    = "data"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 500
            volume_type           = "gp3"
            iops                  = 16000
            throughput            = 1000
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
      
      tags = {
        NodeGroup = "data"
      }
    }
    
    # Gateway node group
    gateway = {
      name            = "gateway-node-group"
      use_name_prefix = false
      
      min_size     = 2
      max_size     = 10
      desired_size = 3
      
      instance_types = ["c5.xlarge"]
      capacity_type  = "ON_DEMAND"
      
      subnet_ids = module.vpc.public_subnets  # Public subnets for ingress
      
      labels = {
        role = "gateway"
        "node.kubernetes.io/ingress" = "true"
      }
      
      taints = [{
        key    = "gateway"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      
      tags = {
        NodeGroup = "gateway"
      }
    }
  }
  
  # OIDC Provider
  enable_irsa = true
  
  # aws-auth configmap
  manage_aws_auth_configmap = true
  
  tags = {
    Environment = "production"
    GithubRepo  = "dora-compliance"
  }
}

# KMS key for EKS encryption
resource "aws_kms_key" "eks" {
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 10
  enable_key_rotation     = true
  
  tags = {
    Name = "${var.cluster_name}-eks-key"
  }
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${var.cluster_name}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

# EBS CSI Driver IAM Role
module "ebs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.30"
  
  role_name = "${var.cluster_name}-ebs-csi-driver"
  
  attach_ebs_csi_policy = true
  
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}

# EFS CSI Driver IAM Role
module "efs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.30"
  
  role_name = "${var.cluster_name}-efs-csi-driver"
  
  attach_efs_csi_policy = true
  
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:efs-csi-controller-sa"]
    }
  }
}

# Install EKS Add-ons
resource "aws_eks_addon" "vpc_cni" {
  cluster_name             = module.eks.cluster_name
  addon_name               = "vpc-cni"
  addon_version            = "v1.15.1-eksbuild.1"
  resolve_conflicts_on_create = "OVERWRITE"
  
  depends_on = [module.eks]
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name             = module.eks.cluster_name
  addon_name               = "kube-proxy"
  addon_version            = "v1.28.2-eksbuild.2"
  resolve_conflicts_on_create = "OVERWRITE"
  
  depends_on = [module.eks]
}

resource "aws_eks_addon" "coredns" {
  cluster_name             = module.eks.cluster_name
  addon_name               = "coredns"
  addon_version            = "v1.10.1-eksbuild.6"
  resolve_conflicts_on_create = "OVERWRITE"
  
  depends_on = [module.eks]
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name             = module.eks.cluster_name
  addon_name               = "aws-ebs-csi-driver"
  addon_version            = "v1.25.0-eksbuild.1"
  service_account_role_arn = module.ebs_csi_irsa.iam_role_arn
  resolve_conflicts_on_create = "OVERWRITE"
  
  depends_on = [module.eks]
}

# Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "node_groups" {
  description = "Outputs from node groups"
  value       = module.eks.eks_managed_node_groups
} 