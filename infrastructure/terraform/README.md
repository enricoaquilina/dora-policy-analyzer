# DORA Compliance System - Infrastructure as Code

This directory contains the complete Infrastructure-as-Code (IaC) implementation for the DORA Compliance System using Terraform, Kubernetes manifests, and Helm charts.

## Overview

The IaC implementation provides:
- **Complete AWS Infrastructure** - VPC, EKS, databases, security, monitoring
- **Kubernetes Resources** - Namespaces, RBAC, security policies, storage
- **Application Deployment** - Helm charts, service mesh, ingress configuration
- **CI/CD Pipelines** - Automated deployment and validation
- **State Management** - Remote state with locking and encryption
- **Drift Detection** - Automated infrastructure compliance monitoring

## Architecture

```
infrastructure/terraform/
├── environments/           # Environment-specific configurations
│   ├── dev/               # Development environment
│   ├── staging/           # Staging environment
│   └── prod/              # Production environment
├── modules/               # Reusable Terraform modules
│   ├── aws-infrastructure/ # Core AWS resources
│   ├── eks-cluster/       # EKS cluster setup
│   ├── database-cluster/  # Multi-database setup
│   ├── security/          # Security and compliance
│   ├── monitoring/        # Observability stack
│   └── networking/        # VPC and service mesh
├── helm-charts/           # Custom Helm charts
│   ├── dora-agents/       # Agent orchestration
│   ├── compliance-db/     # Database configurations
│   └── monitoring-stack/  # Observability tools
├── kubernetes/            # Raw Kubernetes manifests
│   ├── namespaces/        # Namespace definitions
│   ├── rbac/              # Role-based access control
│   ├── security-policies/ # Pod security policies
│   └── storage/           # Storage classes and PVCs
├── scripts/               # Automation scripts
│   ├── deploy.sh          # Main deployment script
│   ├── validate.sh        # Infrastructure validation
│   ├── destroy.sh         # Clean destruction
│   └── drift-check.sh     # Drift detection
└── pipelines/             # CI/CD pipeline definitions
    ├── github-actions/    # GitHub Actions workflows
    ├── gitlab-ci/         # GitLab CI configurations
    └── jenkins/           # Jenkins pipeline scripts
```

## Prerequisites

### Required Tools
- **Terraform** >= 1.6.0
- **AWS CLI** >= 2.0
- **kubectl** >= 1.28
- **Helm** >= 3.13
- **jq** >= 1.6

### AWS Requirements
- AWS Account with appropriate permissions
- IAM user with administrator access (for initial setup)
- Route 53 hosted zone for domain management
- S3 bucket for Terraform state (will be created if not exists)

### Environment Variables
```bash
# AWS Configuration
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-west-2"
export AWS_PROFILE="dora-compliance"

# Domain Configuration
export DOMAIN_NAME="dora-compliance.com"
export SUBDOMAIN_PREFIX="api"

# Terraform Configuration
export TF_STATE_BUCKET="dora-compliance-terraform-state"
export TF_STATE_REGION="us-west-2"
export TF_LOCK_TABLE="dora-compliance-terraform-locks"

# Application Configuration
export DORA_ENV="prod"  # dev, staging, prod
export CLUSTER_NAME="dora-eks-cluster"
```

## Quick Start

### 1. Initial Setup
```bash
# Clone and navigate to terraform directory
cd infrastructure/terraform

# Set up environment variables
cp environments/prod/terraform.tfvars.example environments/prod/terraform.tfvars
# Edit terraform.tfvars with your specific values

# Initialize Terraform
./scripts/deploy.sh init prod
```

### 2. Deploy Infrastructure
```bash
# Plan the deployment
./scripts/deploy.sh plan prod

# Deploy all infrastructure
./scripts/deploy.sh apply prod

# Validate deployment
./scripts/validate.sh prod
```

### 3. Configure Kubernetes
```bash
# Update kubeconfig
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# Deploy Kubernetes resources
kubectl apply -k kubernetes/overlays/prod/

# Install Helm charts
helm install dora-agents helm-charts/dora-agents/ -n dora-system
```

## Environment Management

### Development Environment
- **Purpose**: Feature development and testing
- **Resources**: Smaller instances, single AZ
- **Data**: Synthetic test data only
- **Security**: Relaxed policies for development efficiency

```bash
./scripts/deploy.sh apply dev
```

### Staging Environment
- **Purpose**: Pre-production testing and validation
- **Resources**: Production-like sizing
- **Data**: Anonymized production data subset
- **Security**: Production-equivalent security

```bash
./scripts/deploy.sh apply staging
```

### Production Environment
- **Purpose**: Live DORA compliance operations
- **Resources**: Full HA across multiple AZs
- **Data**: Live compliance and regulatory data
- **Security**: Maximum security and compliance controls

```bash
./scripts/deploy.sh apply prod
```

## Module Descriptions

### AWS Infrastructure Module
**Location**: `modules/aws-infrastructure/`
**Purpose**: Core AWS resources including VPC, subnets, security groups, and IAM

**Key Resources**:
- VPC with public/private subnets across 3 AZs
- Internet Gateway and NAT Gateways
- Route tables and security groups
- IAM roles and policies for EKS
- KMS keys for encryption

### EKS Cluster Module
**Location**: `modules/eks-cluster/`
**Purpose**: Amazon EKS cluster with node groups and addons

**Key Resources**:
- EKS cluster with managed node groups
- Cluster autoscaler configuration
- EBS and EFS CSI drivers
- Pod identity associations
- IRSA (IAM Roles for Service Accounts)

### Database Cluster Module
**Location**: `modules/database-cluster/`
**Purpose**: Multi-database setup for different data types

**Key Resources**:
- RDS PostgreSQL cluster (primary database)
- ElastiCache Redis cluster (caching)
- DocumentDB cluster (MongoDB compatible)
- Managed Grafana and Prometheus
- Backup and monitoring configurations

### Security Module
**Location**: `modules/security/`
**Purpose**: Comprehensive security and compliance framework

**Key Resources**:
- AWS Systems Manager for secrets
- Security groups and NACLs
- IAM policies and roles
- AWS Config rules for compliance
- CloudTrail for audit logging

### Monitoring Module
**Location**: `modules/monitoring/`
**Purpose**: Observability and monitoring infrastructure

**Key Resources**:
- Amazon Managed Prometheus
- Amazon Managed Grafana
- CloudWatch log groups and alarms
- X-Ray tracing configuration
- SNS topics for alerting

### Networking Module
**Location**: `modules/networking/`
**Purpose**: Advanced networking and service mesh

**Key Resources**:
- Application Load Balancer (ALB)
- Network Load Balancer (NLB)
- Route 53 DNS records
- ACM certificates
- VPC endpoints for AWS services

## State Management

### Remote State Configuration
Terraform state is stored remotely in S3 with DynamoDB locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "dora-compliance-terraform-state"
    key            = "environments/prod/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "dora-compliance-terraform-locks"
    encrypt        = true
  }
}
```

### State Security
- **Encryption**: State files encrypted at rest using S3 KMS
- **Access Control**: IAM policies restrict state access
- **Versioning**: S3 versioning enabled for state history
- **Locking**: DynamoDB prevents concurrent modifications

## CI/CD Integration

### GitHub Actions Workflow
**Location**: `pipelines/github-actions/terraform.yml`

**Features**:
- Automated plan on pull requests
- Automatic apply on main branch merge
- Drift detection on schedule
- Security scanning with Checkov
- Cost estimation with Infracost

### GitLab CI Pipeline
**Location**: `pipelines/gitlab-ci/.gitlab-ci.yml`

**Stages**:
- **Validate**: Terraform fmt and validate
- **Plan**: Generate execution plan
- **Security**: Security and compliance scanning
- **Apply**: Deploy infrastructure changes
- **Test**: Validate deployed resources

### Jenkins Pipeline
**Location**: `pipelines/jenkins/Jenkinsfile`

**Pipeline Steps**:
- Checkout and setup
- Terraform validation
- Security scanning
- Plan and apply
- Post-deployment validation

## Drift Detection

### Automated Monitoring
The system includes automated drift detection to ensure infrastructure compliance:

```bash
# Manual drift check
./scripts/drift-check.sh prod

# Scheduled via cron (daily at 2 AM)
0 2 * * * /path/to/infrastructure/terraform/scripts/drift-check.sh prod
```

### Drift Remediation
1. **Detection**: Compare actual vs. desired state
2. **Analysis**: Identify unauthorized changes
3. **Notification**: Alert operations team
4. **Remediation**: Auto-fix or manual intervention
5. **Documentation**: Log all changes and actions

## Security Best Practices

### Infrastructure Security
- **Least Privilege**: Minimal IAM permissions
- **Encryption**: All data encrypted in transit and at rest
- **Network Isolation**: Private subnets for sensitive resources
- **Monitoring**: Comprehensive logging and alerting

### Terraform Security
- **State Protection**: Encrypted remote state with access controls
- **Secret Management**: No hardcoded secrets in code
- **Validation**: Automated security scanning
- **Audit Trail**: All changes tracked and logged

## Cost Optimization

### Resource Optimization
- **Spot Instances**: For non-critical workloads
- **Reserved Instances**: For predictable workloads
- **Auto Scaling**: Dynamic scaling based on demand
- **Resource Tagging**: Comprehensive cost tracking

### Cost Monitoring
- **Budgets**: AWS Budgets with alerts
- **Cost Explorer**: Regular cost analysis
- **Infracost**: CI/CD cost estimation
- **Resource Cleanup**: Automated cleanup of unused resources

## Disaster Recovery

### Backup Strategy
- **Infrastructure**: Terraform state and configurations
- **Data**: Cross-region database backups
- **Configurations**: Git-based configuration management
- **Documentation**: Runbooks and procedures

### Recovery Procedures
1. **Assessment**: Evaluate damage and requirements
2. **Infrastructure**: Rebuild using Terraform
3. **Data**: Restore from backups
4. **Validation**: Verify system functionality
5. **Documentation**: Update procedures based on experience

## Troubleshooting

### Common Issues

#### Terraform State Lock
```bash
# Check lock status
terraform force-unlock LOCK_ID

# If needed, manually remove from DynamoDB
aws dynamodb delete-item --table-name dora-compliance-terraform-locks --key '{"LockID":{"S":"LOCK_ID"}}'
```

#### EKS Node Group Issues
```bash
# Check node group status
aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name workers

# Update kubeconfig
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
```

#### DNS and Certificate Issues
```bash
# Check Route 53 records
aws route53 list-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID

# Check ACM certificates
aws acm list-certificates --region $AWS_REGION
```

### Validation Commands

```bash
# Validate Terraform configuration
terraform validate

# Check AWS resources
aws eks describe-cluster --name $CLUSTER_NAME
aws rds describe-db-clusters
aws elasticache describe-cache-clusters

# Validate Kubernetes connectivity
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

## Maintenance

### Regular Tasks
- **Weekly**: Review and apply security patches
- **Monthly**: Cost optimization review
- **Quarterly**: Disaster recovery testing
- **Annually**: Full security audit

### Updates and Upgrades
- **Terraform**: Keep providers and modules updated
- **Kubernetes**: Regular cluster upgrades
- **Applications**: Coordinate with application teams
- **Security**: Apply security patches promptly

## Support

### Documentation
- **Architecture**: `../docs/architecture/`
- **Security**: `../docs/security/`
- **Monitoring**: `../docs/monitoring/`
- **Troubleshooting**: `../docs/troubleshooting/`

### Contact Information
- **Infrastructure Team**: infrastructure@dora-compliance.com
- **Security Team**: security@dora-compliance.com
- **On-Call**: Follow escalation procedures in runbooks

---

**Last Updated**: $(date)
**Version**: 1.0.0
**Maintained By**: DORA Compliance Infrastructure Team 