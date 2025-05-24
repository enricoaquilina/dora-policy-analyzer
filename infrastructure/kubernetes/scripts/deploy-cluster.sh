#!/bin/bash
# DORA Compliance System - Kubernetes Cluster Deployment Script

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
    local level=$1
    shift
    local message="$@"
    
    case $level in
        "info")
            echo -e "${GREEN}[INFO]${NC} ${message}"
            ;;
        "warn")
            echo -e "${YELLOW}[WARN]${NC} ${message}"
            ;;
        "error")
            echo -e "${RED}[ERROR]${NC} ${message}"
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log "info" "Checking prerequisites..."
    
    # Check for required tools
    local required_tools=("terraform" "kubectl" "helm" "aws")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log "error" "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log "error" "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    log "info" "All prerequisites met."
}

# Deploy infrastructure
deploy_infrastructure() {
    local environment=$1
    local cluster_dir="infrastructure/kubernetes/clusters/${environment}"
    
    log "info" "Deploying ${environment} cluster..."
    
    if [[ ! -d "$cluster_dir" ]]; then
        log "error" "Cluster directory not found: $cluster_dir"
        exit 1
    fi
    
    cd "$cluster_dir"
    
    # Initialize Terraform
    log "info" "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    log "info" "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    log "info" "Applying Terraform deployment..."
    terraform apply tfplan
    
    # Update kubeconfig
    log "info" "Updating kubeconfig..."
    aws eks update-kubeconfig --name "dora-compliance-${environment}" --region "${AWS_REGION:-eu-west-1}"
    
    cd -
}

# Apply Kubernetes configurations
apply_k8s_configs() {
    log "info" "Applying Kubernetes configurations..."
    
    # Apply namespaces
    log "info" "Creating namespaces..."
    kubectl apply -f infrastructure/kubernetes/namespaces/
    
    # Apply RBAC
    log "info" "Configuring RBAC..."
    kubectl apply -f infrastructure/kubernetes/rbac/
    
    # Apply storage classes
    log "info" "Creating storage classes..."
    kubectl apply -f infrastructure/kubernetes/storage/
    
    # Wait for all namespaces to be active
    log "info" "Waiting for namespaces to be ready..."
    for ns in dora-system dora-agents dora-data dora-monitoring dora-security; do
        kubectl wait --for=condition=Active namespace/$ns --timeout=60s
    done
}

# Install Istio service mesh
install_istio() {
    log "info" "Installing Istio service mesh..."
    
    # Download Istio
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
    
    # Install Istio
    cd istio-1.20.0
    export PATH=$PWD/bin:$PATH
    
    # Install Istio with production profile
    istioctl install --set profile=production -y
    
    # Enable automatic sidecar injection
    kubectl label namespace dora-system istio-injection=enabled
    kubectl label namespace dora-agents istio-injection=enabled
    kubectl label namespace dora-data istio-injection=enabled
    
    cd -
}

# Verify deployment
verify_deployment() {
    log "info" "Verifying deployment..."
    
    # Check nodes
    log "info" "Checking nodes..."
    kubectl get nodes
    
    # Check namespaces
    log "info" "Checking namespaces..."
    kubectl get namespaces | grep dora
    
    # Check storage classes
    log "info" "Checking storage classes..."
    kubectl get storageclass | grep dora
    
    # Check cluster autoscaler
    log "info" "Checking cluster autoscaler..."
    kubectl -n kube-system get deployment cluster-autoscaler
    
    # Check metrics server
    log "info" "Checking metrics server..."
    kubectl -n kube-system get deployment metrics-server
}

# Main function
main() {
    local environment="${1:-production}"
    
    log "info" "Starting DORA Compliance Kubernetes cluster deployment"
    log "info" "Environment: ${environment}"
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy infrastructure
    deploy_infrastructure "$environment"
    
    # Apply Kubernetes configurations
    apply_k8s_configs
    
    # Install Istio
    if [[ "$environment" == "production" ]]; then
        install_istio
    fi
    
    # Verify deployment
    verify_deployment
    
    log "info" "Deployment completed successfully!"
    log "info" "Cluster endpoint: $(kubectl config current-context)"
    log "info" "You can now deploy applications to the cluster."
}

# Run main function
main "$@" 