#!/bin/bash
# DORA Compliance System - Network Infrastructure Setup Script

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT="600s"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETWORK_DIR="$(dirname "$SCRIPT_DIR")"

# Component versions
ISTIO_VERSION="1.20.1"
AWS_LB_CONTROLLER_VERSION="1.6.2"
EXTERNAL_DNS_VERSION="1.13.1"
CERT_MANAGER_VERSION="v1.13.3"
NGINX_INGRESS_VERSION="4.8.3"

# AWS configuration (to be set via environment variables)
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-""}
AWS_REGION=${AWS_REGION:-"us-west-2"}
VPC_ID=${VPC_ID:-""}
DOMAIN_NAME=${DOMAIN_NAME:-"dora-compliance.com"}

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
        "debug")
            echo -e "${BLUE}[DEBUG]${NC} ${message}"
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log "info" "Checking network setup prerequisites..."
    
    # Check for required tools
    local required_tools=("kubectl" "helm" "istioctl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log "error" "$tool is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check kubectl context
    local current_context=$(kubectl config current-context 2>/dev/null || echo "none")
    if [[ "$current_context" == "none" ]]; then
        log "error" "No kubectl context set. Please configure kubectl."
        exit 1
    fi
    
    log "info" "Using kubectl context: $current_context"
    
    # Check AWS configuration
    if [[ -z "$AWS_ACCOUNT_ID" ]]; then
        log "warn" "AWS_ACCOUNT_ID not set. Some features may not work correctly."
    fi
    
    if [[ -z "$VPC_ID" ]]; then
        log "warn" "VPC_ID not set. Load balancer configuration may need manual adjustment."
    fi
    
    log "info" "All prerequisites checked."
}

# Install cert-manager (required for TLS certificates)
install_cert_manager() {
    log "info" "Installing cert-manager for certificate management..."
    
    # Add cert-manager Helm repository
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Create cert-manager namespace
    kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
    
    # Install cert-manager
    if ! helm list -n cert-manager | grep -q "cert-manager"; then
        helm install cert-manager jetstack/cert-manager \
            --namespace cert-manager \
            --version "$CERT_MANAGER_VERSION" \
            --set installCRDs=true \
            --set global.leaderElection.namespace=cert-manager \
            --timeout "$TIMEOUT"
    else
        log "warn" "cert-manager already installed."
    fi
    
    # Wait for cert-manager to be ready
    log "info" "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=Available deployment/cert-manager \
        -n cert-manager --timeout="$TIMEOUT"
    kubectl wait --for=condition=Available deployment/cert-manager-cainjector \
        -n cert-manager --timeout="$TIMEOUT"
    kubectl wait --for=condition=Available deployment/cert-manager-webhook \
        -n cert-manager --timeout="$TIMEOUT"
    
    log "info" "cert-manager installation completed."
}

# Install AWS Load Balancer Controller
install_aws_load_balancer_controller() {
    log "info" "Installing AWS Load Balancer Controller..."
    
    # Add EKS Helm repository
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    
    # Create service account with IRSA
    if [[ -n "$AWS_ACCOUNT_ID" ]]; then
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  labels:
    app.kubernetes.io/name: aws-load-balancer-controller
    app.kubernetes.io/part-of: dora-compliance
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::$AWS_ACCOUNT_ID:role/AmazonEKSLoadBalancerControllerRole
EOF
    fi
    
    # Install AWS Load Balancer Controller
    if ! helm list -n kube-system | grep -q "aws-load-balancer-controller"; then
        helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
            --namespace kube-system \
            --set clusterName=dora-eks-cluster \
            --set serviceAccount.create=false \
            --set serviceAccount.name=aws-load-balancer-controller \
            --set region="$AWS_REGION" \
            --set vpcId="$VPC_ID" \
            --timeout "$TIMEOUT"
    else
        log "warn" "AWS Load Balancer Controller already installed."
    fi
    
    # Wait for controller to be ready
    log "info" "Waiting for AWS Load Balancer Controller to be ready..."
    kubectl wait --for=condition=Available deployment/aws-load-balancer-controller \
        -n kube-system --timeout="$TIMEOUT"
    
    log "info" "AWS Load Balancer Controller installation completed."
}

# Install External DNS
install_external_dns() {
    log "info" "Installing External DNS..."
    
    # Add External DNS Helm repository
    helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
    helm repo update
    
    # Create External DNS values file
    cat > /tmp/external-dns-values.yaml << EOF
# External DNS configuration
image:
  tag: "$EXTERNAL_DNS_VERSION"

provider: aws

# AWS configuration
aws:
  region: $AWS_REGION
  zoneType: public
  assumeRoleArn: ${AWS_ACCOUNT_ID:+arn:aws:iam::$AWS_ACCOUNT_ID:role/ExternalDNSRole}

# Domain filter
domainFilters:
- $DOMAIN_NAME

# Source configuration
sources:
- service
- ingress
- istio-gateway
- istio-virtualservice

# Policy
policy: sync

# Registry
registry: txt
txtOwnerId: dora-k8s-cluster
txtPrefix: dora-

# Logging
logLevel: info
logFormat: json

# Resource allocation
resources:
  requests:
    cpu: 50m
    memory: 50Mi
  limits:
    cpu: 100m
    memory: 100Mi

# Security
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  fsGroup: 65534

# ServiceMonitor
serviceMonitor:
  enabled: true
  labels:
    app.kubernetes.io/part-of: dora-compliance

# Node placement
nodeSelector:
  role: system

tolerations:
- key: "system"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
EOF
    
    # Install External DNS
    if ! helm list -n kube-system | grep -q "external-dns"; then
        helm install external-dns external-dns/external-dns \
            --namespace kube-system \
            --values /tmp/external-dns-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "External DNS already installed."
    fi
    
    # Wait for External DNS to be ready
    log "info" "Waiting for External DNS to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=external-dns \
        -n kube-system --timeout="$TIMEOUT"
    
    log "info" "External DNS installation completed."
}

# Install Istio service mesh
install_istio() {
    log "info" "Installing Istio service mesh..."
    
    # Check if istioctl is available and correct version
    local installed_version=$(istioctl version --client --short 2>/dev/null || echo "none")
    if [[ "$installed_version" != *"$ISTIO_VERSION"* ]]; then
        log "warn" "istioctl version $ISTIO_VERSION not found. Please install the correct version."
    fi
    
    # Create istio-system namespace
    kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Istio using the configuration file
    log "info" "Applying Istio configuration..."
    kubectl apply -f "$NETWORK_DIR/service-mesh/istio/installation/istio-installation.yaml"
    
    # Wait for Istio control plane to be ready
    log "info" "Waiting for Istio control plane to be ready..."
    kubectl wait --for=condition=Ready pod -l app=istiod \
        -n istio-system --timeout="$TIMEOUT"
    
    # Wait for ingress gateway to be ready
    log "info" "Waiting for Istio ingress gateway to be ready..."
    kubectl wait --for=condition=Ready pod -l app=istio-ingressgateway \
        -n istio-system --timeout="$TIMEOUT"
    
    log "info" "Istio installation completed."
}

# Configure namespace injection
configure_namespace_injection() {
    log "info" "Configuring Istio sidecar injection for namespaces..."
    
    # Enable sidecar injection for application namespaces
    local namespaces=("dora-system" "dora-agents" "dora-data")
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            kubectl label namespace "$ns" istio-injection=enabled --overwrite
            log "info" "Enabled Istio injection for namespace: $ns"
        else
            log "warn" "Namespace $ns does not exist, skipping injection configuration."
        fi
    done
    
    # Disable injection for monitoring and security namespaces (they have their own mesh)
    local no_injection_namespaces=("dora-monitoring" "dora-security" "kube-system" "cert-manager")
    for ns in "${no_injection_namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            kubectl label namespace "$ns" istio-injection=disabled --overwrite
            log "info" "Disabled Istio injection for namespace: $ns"
        fi
    done
}

# Install NGINX Ingress Controller (alternative/backup)
install_nginx_ingress() {
    log "info" "Installing NGINX Ingress Controller as backup..."
    
    # Add NGINX Helm repository
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    
    # Create NGINX values file
    cat > /tmp/nginx-values.yaml << EOF
# NGINX Ingress Controller configuration
controller:
  # Resource allocation
  resources:
    requests:
      cpu: 100m
      memory: 90Mi
    limits:
      cpu: 500m
      memory: 500Mi
  
  # Replica count
  replicaCount: 3
  
  # Service configuration
  service:
    type: LoadBalancer
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
      service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
      service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
      external-dns.alpha.kubernetes.io/hostname: "nginx.$DOMAIN_NAME"
  
  # Configuration
  config:
    use-proxy-protocol: "true"
    use-forwarded-headers: "true"
    compute-full-forwarded-for: "true"
    proxy-real-ip-cidr: "10.0.0.0/16"
    ssl-protocols: "TLSv1.3 TLSv1.2"
    ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
    enable-brotli: "true"
    
  # Metrics
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
      additionalLabels:
        app.kubernetes.io/part-of: dora-compliance
  
  # Pod placement
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app.kubernetes.io/name: ingress-nginx
        topologyKey: kubernetes.io/hostname
  
  nodeSelector:
    role: gateway
  
  tolerations:
  - key: "gateway"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"

# Default backend
defaultBackend:
  enabled: true
  resources:
    requests:
      cpu: 10m
      memory: 20Mi
    limits:
      cpu: 50m
      memory: 50Mi
EOF
    
    # Install NGINX Ingress Controller
    if ! helm list -n ingress-nginx | grep -q "ingress-nginx"; then
        kubectl create namespace ingress-nginx --dry-run=client -o yaml | kubectl apply -f -
        
        helm install ingress-nginx ingress-nginx/ingress-nginx \
            --namespace ingress-nginx \
            --values /tmp/nginx-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "NGINX Ingress Controller already installed."
    fi
    
    # Wait for NGINX to be ready
    log "info" "Waiting for NGINX Ingress Controller to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=ingress-nginx \
        -n ingress-nginx --timeout="$TIMEOUT"
    
    log "info" "NGINX Ingress Controller installation completed."
}

# Create ClusterIssuer for Let's Encrypt certificates
create_cluster_issuer() {
    log "info" "Creating ClusterIssuer for SSL certificates..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: dora-compliance
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@$DOMAIN_NAME
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - dns01:
        route53:
          region: $AWS_REGION
          hostedZoneID: # Will be auto-discovered
      selector:
        dnsZones:
        - "$DOMAIN_NAME"
EOF
    
    # Create staging issuer for testing
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: dora-compliance
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@$DOMAIN_NAME
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - dns01:
        route53:
          region: $AWS_REGION
          hostedZoneID: # Will be auto-discovered
      selector:
        dnsZones:
        - "$DOMAIN_NAME"
EOF
    
    log "info" "ClusterIssuer creation completed."
}

# Create network policies for enhanced security
create_network_policies() {
    log "info" "Creating network policies for enhanced security..."
    
    # Network policy for Istio ingress gateway
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: istio-ingressgateway-network-policy
  namespace: istio-system
  labels:
    app.kubernetes.io/name: istio
    app.kubernetes.io/part-of: dora-compliance
spec:
  podSelector:
    matchLabels:
      app: istio-ingressgateway
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow traffic from internet
  - from: []
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 8443
    - protocol: TCP
      port: 15021
  egress:
  # Allow traffic to application namespaces
  - to:
    - namespaceSelector:
        matchLabels:
          istio-injection: enabled
  # Allow DNS resolution
  - to: []
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
EOF
    
    log "info" "Network policies creation completed."
}

# Verify network deployment
verify_network() {
    log "info" "Verifying network infrastructure deployment..."
    
    # Check cert-manager
    local cert_manager_pods=$(kubectl get pods -n cert-manager --no-headers | grep "Running" | wc -l)
    if [[ "$cert_manager_pods" -ge 3 ]]; then
        log "info" "✓ cert-manager is running ($cert_manager_pods pods)"
    else
        log "warn" "✗ cert-manager: only $cert_manager_pods pods running"
    fi
    
    # Check AWS Load Balancer Controller
    local aws_lb_pods=$(kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --no-headers | grep "Running" | wc -l)
    if [[ "$aws_lb_pods" -ge 1 ]]; then
        log "info" "✓ AWS Load Balancer Controller is running ($aws_lb_pods pods)"
    else
        log "warn" "✗ AWS Load Balancer Controller is not running"
    fi
    
    # Check External DNS
    local external_dns_pods=$(kubectl get pods -n kube-system -l app.kubernetes.io/name=external-dns --no-headers | grep "Running" | wc -l)
    if [[ "$external_dns_pods" -ge 1 ]]; then
        log "info" "✓ External DNS is running ($external_dns_pods pods)"
    else
        log "warn" "✗ External DNS is not running"
    fi
    
    # Check Istio
    local istio_control_pods=$(kubectl get pods -n istio-system -l app=istiod --no-headers | grep "Running" | wc -l)
    if [[ "$istio_control_pods" -ge 3 ]]; then
        log "info" "✓ Istio control plane is running ($istio_control_pods pods)"
    else
        log "warn" "✗ Istio control plane: only $istio_control_pods pods running"
    fi
    
    local istio_gateway_pods=$(kubectl get pods -n istio-system -l app=istio-ingressgateway --no-headers | grep "Running" | wc -l)
    if [[ "$istio_gateway_pods" -ge 3 ]]; then
        log "info" "✓ Istio ingress gateway is running ($istio_gateway_pods pods)"
    else
        log "warn" "✗ Istio ingress gateway: only $istio_gateway_pods pods running"
    fi
    
    # Check NGINX Ingress
    local nginx_pods=$(kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --no-headers | grep "Running" 2>/dev/null | wc -l)
    if [[ "$nginx_pods" -ge 3 ]]; then
        log "info" "✓ NGINX Ingress Controller is running ($nginx_pods pods)"
    else
        log "info" "ℹ NGINX Ingress Controller: $nginx_pods pods (optional component)"
    fi
    
    # Display service endpoints
    log "info" "Network service endpoints:"
    
    # Get Istio ingress gateway external IP
    local istio_external_ip=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    echo "  Istio Ingress Gateway: $istio_external_ip"
    
    # Get NGINX ingress external IP
    local nginx_external_ip=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "not deployed")
    echo "  NGINX Ingress Controller: $nginx_external_ip"
    
    log "info" "Network infrastructure verification completed."
}

# Display post-installation information
display_post_install_info() {
    log "info" "Network infrastructure deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Configure DNS records for your domain ($DOMAIN_NAME)"
    echo "2. Deploy application workloads with Istio sidecar injection"
    echo "3. Create Gateway and VirtualService resources for traffic routing"
    echo "4. Configure SSL certificates using cert-manager"
    echo "5. Set up monitoring and alerting for network components"
    echo ""
    echo "Useful commands:"
    echo "  # Check Istio installation"
    echo "  istioctl analyze"
    echo ""
    echo "  # View Istio configuration"
    echo "  istioctl proxy-config cluster <pod-name> -n <namespace>"
    echo ""
    echo "  # Check certificate status"
    echo "  kubectl get certificates --all-namespaces"
    echo ""
    echo "  # View ingress gateway logs"
    echo "  kubectl logs -l app=istio-ingressgateway -n istio-system"
}

# Clean up temporary files
cleanup() {
    log "info" "Cleaning up temporary files..."
    rm -f /tmp/external-dns-values.yaml /tmp/nginx-values.yaml
}

# Main function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "info" "Starting DORA network infrastructure deployment..."
            check_prerequisites
            install_cert_manager
            install_aws_load_balancer_controller
            install_external_dns
            install_istio
            configure_namespace_injection
            install_nginx_ingress
            create_cluster_issuer
            create_network_policies
            verify_network
            display_post_install_info
            cleanup
            ;;
        "verify")
            log "info" "Verifying network infrastructure..."
            verify_network
            ;;
        "cleanup")
            log "info" "Cleaning up temporary files..."
            cleanup
            ;;
        *)
            echo "Usage: $0 [deploy|verify|cleanup]"
            echo "  deploy: Full network infrastructure deployment (default)"
            echo "  verify: Verify network deployment status"
            echo "  cleanup: Clean up temporary files"
            echo ""
            echo "Environment variables:"
            echo "  AWS_ACCOUNT_ID: AWS account ID for IRSA configuration"
            echo "  AWS_REGION: AWS region (default: us-west-2)"
            echo "  VPC_ID: VPC ID for load balancer configuration"
            echo "  DOMAIN_NAME: Domain name for DNS configuration (default: dora-compliance.com)"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@" 