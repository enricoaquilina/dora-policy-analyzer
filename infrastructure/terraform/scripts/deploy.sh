#!/bin/bash
# DORA Compliance System - Infrastructure Deployment Script
# Automated deployment and management of Terraform infrastructure

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$TERRAFORM_DIR")")"

# Default values
ENVIRONMENT=""
ACTION=""
AUTO_APPROVE=false
DESTROY_PROTECTION=true
VERBOSE=false
DRY_RUN=false

# Function to print colored output
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "info")
            echo -e "${timestamp} ${GREEN}[INFO]${NC} ${message}"
            ;;
        "warn")
            echo -e "${timestamp} ${YELLOW}[WARN]${NC} ${message}"
            ;;
        "error")
            echo -e "${timestamp} ${RED}[ERROR]${NC} ${message}"
            ;;
        "debug")
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${timestamp} ${BLUE}[DEBUG]${NC} ${message}"
            fi
            ;;
        "success")
            echo -e "${timestamp} ${GREEN}[SUCCESS]${NC} ${message}"
            ;;
        "header")
            echo -e "\n${PURPLE}========================================${NC}"
            echo -e "${PURPLE} ${message}${NC}"
            echo -e "${PURPLE}========================================${NC}\n"
            ;;
    esac
}

# Function to display usage
usage() {
    cat << EOF
DORA Compliance System - Infrastructure Deployment Script

USAGE:
    $(basename "$0") <action> <environment> [options]

ACTIONS:
    init        Initialize Terraform backend and providers
    plan        Generate and show an execution plan
    apply       Apply the Terraform configuration
    destroy     Destroy the Terraform-managed infrastructure
    validate    Validate the Terraform configuration
    fmt         Format Terraform files
    output      Show Terraform outputs
    refresh     Refresh Terraform state
    import      Import existing resources
    state       Manage Terraform state

ENVIRONMENTS:
    dev         Development environment
    staging     Staging environment  
    prod        Production environment

OPTIONS:
    -a, --auto-approve     Auto approve Terraform actions
    -v, --verbose          Enable verbose output
    -d, --dry-run         Show what would be done without executing
    -f, --force           Disable destroy protection (dangerous!)
    -h, --help            Show this help message

EXAMPLES:
    $(basename "$0") init prod
    $(basename "$0") plan dev --verbose
    $(basename "$0") apply staging --auto-approve
    $(basename "$0") destroy dev --force
    $(basename "$0") output prod

ENVIRONMENT VARIABLES:
    AWS_PROFILE           AWS profile to use
    AWS_REGION            AWS region (default: us-west-2)
    TF_VAR_*             Terraform variables
    DORA_ENV             Override environment detection

EOF
}

# Function to check prerequisites
check_prerequisites() {
    log "info" "Checking deployment prerequisites..."
    
    local required_tools=("terraform" "aws" "jq")
    local missing_tools=()
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log "error" "Missing required tools: ${missing_tools[*]}"
        log "error" "Please install the missing tools and try again."
        exit 1
    fi
    
    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r '.terraform_version')
    local min_version="1.6.0"
    
    if ! printf '%s\n' "$min_version" "$tf_version" | sort -C -V; then
        log "warn" "Terraform version $tf_version is older than recommended $min_version"
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log "error" "AWS credentials not configured or invalid"
        log "info" "Please run 'aws configure' or set appropriate environment variables"
        exit 1
    fi
    
    # Check environment file
    local env_file="${TERRAFORM_DIR}/environments/${ENVIRONMENT}/terraform.tfvars"
    if [[ ! -f "$env_file" ]]; then
        log "error" "Environment file not found: $env_file"
        log "info" "Please create the environment configuration file"
        exit 1
    fi
    
    # Check backend config
    local backend_file="${TERRAFORM_DIR}/environments/${ENVIRONMENT}/backend.tfvars"
    if [[ ! -f "$backend_file" ]]; then
        log "error" "Backend configuration not found: $backend_file"
        log "info" "Please create the backend configuration file"
        exit 1
    fi
    
    log "success" "All prerequisites satisfied"
}

# Function to setup environment
setup_environment() {
    log "info" "Setting up environment for: $ENVIRONMENT"
    
    # Change to terraform directory
    cd "$TERRAFORM_DIR"
    
    # Set backend configuration
    local backend_file="environments/${ENVIRONMENT}/backend.tfvars"
    
    # Export environment variables
    export TF_VAR_environment="$ENVIRONMENT"
    export TF_DATA_DIR=".terraform-${ENVIRONMENT}"
    
    # Load environment-specific variables if they exist
    local env_vars_file="environments/${ENVIRONMENT}/.env"
    if [[ -f "$env_vars_file" ]]; then
        log "debug" "Loading environment variables from: $env_vars_file"
        set -a
        source "$env_vars_file"
        set +a
    fi
    
    log "debug" "Terraform data directory: $TF_DATA_DIR"
    log "debug" "Backend configuration: $backend_file"
}

# Function to initialize Terraform
terraform_init() {
    log "header" "Initializing Terraform for $ENVIRONMENT"
    
    local backend_file="environments/${ENVIRONMENT}/backend.tfvars"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would initialize Terraform with backend config: $backend_file"
        return 0
    fi
    
    # Remove existing .terraform directory if it exists and is for different environment
    if [[ -d ".terraform" ]] && [[ ! -d "$TF_DATA_DIR" ]]; then
        log "warn" "Removing existing .terraform directory for clean initialization"
        rm -rf .terraform
    fi
    
    terraform init \
        -backend-config="$backend_file" \
        -upgrade \
        -input=false
    
    log "success" "Terraform initialization completed"
}

# Function to validate Terraform configuration
terraform_validate() {
    log "header" "Validating Terraform Configuration"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would validate Terraform configuration"
        return 0
    fi
    
    terraform validate
    
    log "success" "Terraform configuration is valid"
}

# Function to format Terraform files
terraform_fmt() {
    log "header" "Formatting Terraform Files"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would format Terraform files"
        terraform fmt -check -diff -recursive
        return 0
    fi
    
    terraform fmt -recursive
    
    log "success" "Terraform files formatted"
}

# Function to plan Terraform deployment
terraform_plan() {
    log "header" "Planning Terraform Deployment for $ENVIRONMENT"
    
    local var_file="environments/${ENVIRONMENT}/terraform.tfvars"
    local plan_file="terraform-${ENVIRONMENT}.tfplan"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would create Terraform plan with vars: $var_file"
        return 0
    fi
    
    terraform plan \
        -var-file="$var_file" \
        -out="$plan_file" \
        -input=false \
        -detailed-exitcode
    
    local plan_exit_code=$?
    
    case $plan_exit_code in
        0)
            log "info" "No changes detected in Terraform plan"
            ;;
        1)
            log "error" "Terraform plan failed"
            exit 1
            ;;
        2)
            log "info" "Changes detected in Terraform plan"
            log "info" "Plan saved to: $plan_file"
            ;;
    esac
    
    return $plan_exit_code
}

# Function to apply Terraform configuration
terraform_apply() {
    log "header" "Applying Terraform Configuration for $ENVIRONMENT"
    
    local var_file="environments/${ENVIRONMENT}/terraform.tfvars"
    local plan_file="terraform-${ENVIRONMENT}.tfplan"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would apply Terraform configuration"
        return 0
    fi
    
    # Check for existing plan file
    if [[ -f "$plan_file" ]]; then
        log "info" "Applying existing plan: $plan_file"
        if [[ "$AUTO_APPROVE" == "true" ]]; then
            terraform apply "$plan_file"
        else
            terraform apply "$plan_file"
        fi
    else
        log "info" "No plan file found, creating and applying new plan"
        if [[ "$AUTO_APPROVE" == "true" ]]; then
            terraform apply \
                -var-file="$var_file" \
                -input=false \
                -auto-approve
        else
            terraform apply \
                -var-file="$var_file" \
                -input=false
        fi
    fi
    
    log "success" "Terraform apply completed successfully"
    
    # Clean up plan file
    if [[ -f "$plan_file" ]]; then
        rm "$plan_file"
        log "debug" "Cleaned up plan file: $plan_file"
    fi
}

# Function to destroy Terraform infrastructure
terraform_destroy() {
    log "header" "Destroying Terraform Infrastructure for $ENVIRONMENT"
    
    # Destroy protection check
    if [[ "$DESTROY_PROTECTION" == "true" ]] && [[ "$ENVIRONMENT" == "prod" ]]; then
        log "error" "Destroy protection is enabled for production environment"
        log "error" "Use --force flag to override (THIS IS DANGEROUS!)"
        exit 1
    fi
    
    local var_file="environments/${ENVIRONMENT}/terraform.tfvars"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would destroy Terraform infrastructure"
        return 0
    fi
    
    # Additional confirmation for production
    if [[ "$ENVIRONMENT" == "prod" ]] && [[ "$AUTO_APPROVE" != "true" ]]; then
        echo -n -e "${RED}WARNING: You are about to destroy PRODUCTION infrastructure!${NC}\n"
        echo -n "Type 'yes' to confirm: "
        read -r confirmation
        if [[ "$confirmation" != "yes" ]]; then
            log "info" "Destruction cancelled by user"
            exit 0
        fi
    fi
    
    if [[ "$AUTO_APPROVE" == "true" ]]; then
        terraform destroy \
            -var-file="$var_file" \
            -input=false \
            -auto-approve
    else
        terraform destroy \
            -var-file="$var_file" \
            -input=false
    fi
    
    log "success" "Terraform destroy completed"
}

# Function to show Terraform outputs
terraform_output() {
    log "header" "Terraform Outputs for $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would show Terraform outputs"
        return 0
    fi
    
    terraform output -json | jq '.'
}

# Function to refresh Terraform state
terraform_refresh() {
    log "header" "Refreshing Terraform State for $ENVIRONMENT"
    
    local var_file="environments/${ENVIRONMENT}/terraform.tfvars"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would refresh Terraform state"
        return 0
    fi
    
    terraform refresh \
        -var-file="$var_file" \
        -input=false
    
    log "success" "Terraform state refreshed"
}

# Function to manage Terraform state
terraform_state() {
    log "header" "Terraform State Management for $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "info" "DRY RUN: Would show Terraform state operations"
        terraform state list
        return 0
    fi
    
    echo "Available state operations:"
    echo "  list     - List resources in state"
    echo "  show     - Show specific resource"
    echo "  mv       - Move resource"
    echo "  rm       - Remove resource from state"
    echo "  pull     - Pull current state"
    echo "  push     - Push state to remote"
    echo ""
    echo -n "Enter operation (or 'exit'): "
    read -r operation
    
    case "$operation" in
        "list")
            terraform state list
            ;;
        "show")
            echo -n "Enter resource name: "
            read -r resource
            terraform state show "$resource"
            ;;
        "mv")
            echo -n "Enter source resource: "
            read -r source
            echo -n "Enter destination resource: "
            read -r dest
            terraform state mv "$source" "$dest"
            ;;
        "rm")
            echo -n "Enter resource to remove: "
            read -r resource
            terraform state rm "$resource"
            ;;
        "pull")
            terraform state pull
            ;;
        "push")
            terraform state push
            ;;
        "exit")
            return 0
            ;;
        *)
            log "error" "Unknown operation: $operation"
            exit 1
            ;;
    esac
}

# Function to run security checks
run_security_checks() {
    log "info" "Running security checks..."
    
    # Check for sensitive data in tfvars files
    local var_file="environments/${ENVIRONMENT}/terraform.tfvars"
    if grep -E "(password|secret|key)" "$var_file" | grep -v "kms_key"; then
        log "warn" "Potential sensitive data found in tfvars file"
    fi
    
    # Check for public resource exposure
    if terraform plan -var-file="$var_file" 2>/dev/null | grep -i "public"; then
        log "info" "Public resources detected - please review for security"
    fi
    
    log "success" "Security checks completed"
}

# Function to create environment template
create_environment_template() {
    local env=$1
    local env_dir="${TERRAFORM_DIR}/environments/${env}"
    
    if [[ -d "$env_dir" ]]; then
        log "error" "Environment directory already exists: $env_dir"
        return 1
    fi
    
    log "info" "Creating environment template for: $env"
    
    mkdir -p "$env_dir"
    
    # Create terraform.tfvars template
    cat > "$env_dir/terraform.tfvars" << EOF
# DORA Compliance System - $env Environment Configuration

# Basic Configuration
environment    = "$env"
aws_region     = "us-west-2"
owner_email    = "admin@example.com"
cost_center    = "DORA-COMPLIANCE"

# Network Configuration
vpc_cidr             = "10.0.0.0/16"
domain_name          = "example.com"
subdomain_prefix     = "api"

# EKS Configuration
eks_cluster_version = "1.28"

# Database Configuration
rds_instance_class      = "db.r6g.large"
redis_node_type         = "cache.r6g.large"
documentdb_instance_class = "db.r6g.large"

# Security Configuration
kms_deletion_window      = 7
enable_deletion_protection = true
enable_encryption        = true

# Monitoring Configuration
enable_monitoring    = true
log_retention_days   = 30

# Backup Configuration
backup_retention_period = 30
backup_window          = "03:00-04:00"
maintenance_window     = "sun:05:00-sun:06:00"

# Application Configuration
enable_istio        = true
enable_cert_manager = true
enable_external_dns = true

# Scaling Configuration
auto_scaling_enabled     = true
spot_instance_percentage = 20

# Advanced Configuration
enable_cross_region_backup = false
secondary_region          = "us-east-1"
EOF

    # Create backend.tfvars template
    cat > "$env_dir/backend.tfvars" << EOF
# Terraform Backend Configuration for $env Environment

bucket         = "dora-compliance-terraform-state-$env"
key            = "environments/$env/terraform.tfstate"
region         = "us-west-2"
dynamodb_table = "dora-compliance-terraform-locks-$env"
encrypt        = true
EOF

    # Create .env template
    cat > "$env_dir/.env.example" << EOF
# Environment Variables for $env Environment
# Copy to .env and update with actual values

# AWS Configuration
AWS_PROFILE=dora-compliance
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=123456789012

# Domain Configuration  
DOMAIN_NAME=example.com
SUBDOMAIN_PREFIX=api

# Terraform Configuration
TF_STATE_BUCKET=dora-compliance-terraform-state-$env
TF_STATE_REGION=us-west-2
TF_LOCK_TABLE=dora-compliance-terraform-locks-$env

# Application Configuration
DORA_ENV=$env
CLUSTER_NAME=dora-eks-cluster-$env
EOF

    log "success" "Environment template created: $env_dir"
    log "info" "Please update the configuration files with your specific values"
}

# Parse command line arguments
parse_arguments() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    ACTION="$1"
    shift
    
    # Special case for help
    if [[ "$ACTION" == "help" ]] || [[ "$ACTION" == "-h" ]] || [[ "$ACTION" == "--help" ]]; then
        usage
        exit 0
    fi
    
    # Special case for creating environment template
    if [[ "$ACTION" == "create-env" ]]; then
        if [[ $# -eq 0 ]]; then
            log "error" "Environment name required for create-env action"
            exit 1
        fi
        create_environment_template "$1"
        exit 0
    fi
    
    # Validate action
    case "$ACTION" in
        init|plan|apply|destroy|validate|fmt|output|refresh|state)
            ;;
        *)
            log "error" "Invalid action: $ACTION"
            usage
            exit 1
            ;;
    esac
    
    # Get environment
    if [[ $# -eq 0 ]]; then
        log "error" "Environment required"
        usage
        exit 1
    fi
    
    ENVIRONMENT="$1"
    shift
    
    # Validate environment
    case "$ENVIRONMENT" in
        dev|staging|prod)
            ;;
        *)
            log "error" "Invalid environment: $ENVIRONMENT"
            log "error" "Valid environments: dev, staging, prod"
            exit 1
            ;;
    esac
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--auto-approve)
                AUTO_APPROVE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                DESTROY_PROTECTION=false
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log "error" "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    log "header" "DORA Compliance System Infrastructure Deployment"
    
    parse_arguments "$@"
    
    log "info" "Action: $ACTION"
    log "info" "Environment: $ENVIRONMENT"
    log "debug" "Auto-approve: $AUTO_APPROVE"
    log "debug" "Dry-run: $DRY_RUN"
    log "debug" "Verbose: $VERBOSE"
    
    check_prerequisites
    setup_environment
    
    case "$ACTION" in
        init)
            terraform_init
            ;;
        validate)
            terraform_validate
            ;;
        fmt)
            terraform_fmt
            ;;
        plan)
            terraform_validate
            terraform_plan
            ;;
        apply)
            terraform_validate
            run_security_checks
            terraform_plan
            terraform_apply
            ;;
        destroy)
            terraform_destroy
            ;;
        output)
            terraform_output
            ;;
        refresh)
            terraform_refresh
            ;;
        state)
            terraform_state
            ;;
    esac
    
    log "success" "Deployment script completed successfully"
}

# Execute main function with all arguments
main "$@" 