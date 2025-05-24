#!/bin/bash
# DORA Compliance System - Security Infrastructure Setup Script

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECURITY_NAMESPACE="dora-security"
TIMEOUT="600s"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECURITY_DIR="$(dirname "$SCRIPT_DIR")"

# Security component versions
VAULT_OPERATOR_VERSION="1.20.0"
CERT_MANAGER_VERSION="v1.13.3"
FALCO_VERSION="4.0.0"
OPA_GATEKEEPER_VERSION="3.14.0"

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
    log "info" "Checking security setup prerequisites..."
    
    # Check for required tools
    local required_tools=("kubectl" "helm" "openssl")
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
    
    # Verify all required namespaces exist
    local required_namespaces=("dora-system" "dora-agents" "dora-data" "dora-monitoring" "dora-security")
    for ns in "${required_namespaces[@]}"; do
        if ! kubectl get namespace "$ns" &> /dev/null; then
            log "error" "Namespace '$ns' does not exist. Please create it first."
            exit 1
        fi
    done
    
    log "info" "All prerequisites met."
}

# Install cert-manager for certificate management
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
            --set extraArgs='{--dns01-recursive-nameservers-only,--dns01-recursive-nameservers=8.8.8.8:53\,1.1.1.1:53}' \
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

# Create root CA certificate
create_root_ca() {
    log "info" "Creating root CA certificate..."
    
    # Create CA private key
    if [[ ! -f "/tmp/ca-key.pem" ]]; then
        openssl genrsa -out /tmp/ca-key.pem 4096
    fi
    
    # Create CA certificate
    if [[ ! -f "/tmp/ca-cert.pem" ]]; then
        openssl req -new -x509 -days 3650 -key /tmp/ca-key.pem -out /tmp/ca-cert.pem \
            -subj "/C=US/ST=California/L=San Francisco/O=DORA Compliance/OU=Security/CN=DORA Root CA"
    fi
    
    # Create CA secret in cert-manager namespace
    kubectl create secret tls dora-root-ca-secret \
        --cert=/tmp/ca-cert.pem \
        --key=/tmp/ca-key.pem \
        -n cert-manager \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Create ClusterIssuer
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: dora-ca-issuer
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: dora-compliance
spec:
  ca:
    secretName: dora-root-ca-secret
EOF
    
    log "info" "Root CA certificate created and ClusterIssuer configured."
}

# Install HashiCorp Vault
install_vault() {
    log "info" "Installing HashiCorp Vault..."
    
    # Add Vault Helm repository
    helm repo add hashicorp https://helm.releases.hashicorp.com
    helm repo update
    
    # Install Vault operator
    if ! helm list -n "$SECURITY_NAMESPACE" | grep -q "vault"; then
        # Create Vault TLS certificate
        cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: vault-tls
  namespace: $SECURITY_NAMESPACE
  labels:
    app.kubernetes.io/name: vault
    app.kubernetes.io/part-of: dora-compliance
spec:
  secretName: vault-tls-secret
  issuerRef:
    name: dora-ca-issuer
    kind: ClusterIssuer
  commonName: vault-service.$SECURITY_NAMESPACE.svc.cluster.local
  dnsNames:
  - vault-service
  - vault-service.$SECURITY_NAMESPACE
  - vault-service.$SECURITY_NAMESPACE.svc
  - vault-service.$SECURITY_NAMESPACE.svc.cluster.local
  - dora-vault-cluster-0.dora-vault-cluster
  - dora-vault-cluster-1.dora-vault-cluster
  - dora-vault-cluster-2.dora-vault-cluster
  - dora-vault-cluster-0.dora-vault-cluster.$SECURITY_NAMESPACE.svc.cluster.local
  - dora-vault-cluster-1.dora-vault-cluster.$SECURITY_NAMESPACE.svc.cluster.local
  - dora-vault-cluster-2.dora-vault-cluster.$SECURITY_NAMESPACE.svc.cluster.local
EOF
        
        # Wait for certificate to be ready
        log "info" "Waiting for Vault TLS certificate..."
        kubectl wait --for=condition=Ready certificate/vault-tls \
            -n "$SECURITY_NAMESPACE" --timeout="$TIMEOUT"
        
        # Install Vault with HA configuration
        helm install vault hashicorp/vault \
            --namespace "$SECURITY_NAMESPACE" \
            --set server.ha.enabled=true \
            --set server.ha.replicas=3 \
            --set server.ha.raft.enabled=true \
            --set server.ha.raft.setNodeId=true \
            --set server.auditStorage.enabled=true \
            --set server.auditStorage.size=50Gi \
            --set server.auditStorage.storageClass=dora-fast-ssd \
            --set server.dataStorage.enabled=true \
            --set server.dataStorage.size=100Gi \
            --set server.dataStorage.storageClass=dora-fast-ssd \
            --set server.extraEnvironmentVars.VAULT_CACERT=/vault/userconfig/vault-tls-secret/ca.crt \
            --set server.extraEnvironmentVars.VAULT_TLSCERT=/vault/userconfig/vault-tls-secret/tls.crt \
            --set server.extraEnvironmentVars.VAULT_TLSKEY=/vault/userconfig/vault-tls-secret/tls.key \
            --set server.volumes[0].name=vault-tls \
            --set server.volumes[0].secret.secretName=vault-tls-secret \
            --set server.volumes[0].secret.defaultMode=420 \
            --set server.volumeMounts[0].name=vault-tls \
            --set server.volumeMounts[0].mountPath=/vault/userconfig/vault-tls-secret \
            --set server.volumeMounts[0].readOnly=true \
            --set ui.enabled=true \
            --set ui.serviceType=ClusterIP \
            --timeout "$TIMEOUT"
    else
        log "warn" "Vault already installed."
    fi
    
    # Wait for Vault pods to be ready
    log "info" "Waiting for Vault cluster to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=vault \
        -n "$SECURITY_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Vault installation completed."
}

# Apply default deny network policies
apply_network_policies() {
    log "info" "Applying zero-trust network policies..."
    
    # Apply default deny policies
    kubectl apply -f "$SECURITY_DIR/network-policies/default-deny/"
    
    log "info" "Network policies applied successfully."
}

# Install Falco for runtime security
install_falco() {
    log "info" "Installing Falco for runtime security monitoring..."
    
    # Add Falco Helm repository
    helm repo add falcosecurity https://falcosecurity.github.io/charts
    helm repo update
    
    # Install Falco
    if ! helm list -n "$SECURITY_NAMESPACE" | grep -q "falco"; then
        helm install falco falcosecurity/falco \
            --namespace "$SECURITY_NAMESPACE" \
            --version "$FALCO_VERSION" \
            --set driver.kind=ebpf \
            --set collectors.enabled=true \
            --set collectors.docker.enabled=false \
            --set collectors.containerd.enabled=true \
            --set collectors.crio.enabled=false \
            --set falco.grpc.enabled=true \
            --set falco.grpcOutput.enabled=true \
            --set falco.httpOutput.enabled=true \
            --set falco.jsonOutput=true \
            --set falco.logLevel=INFO \
            --set falco.syscallEventDrops.actions[0]=log \
            --set falco.syscallEventDrops.threshold=0.1 \
            --set falco.syscallEventDrops.rate=0.03333 \
            --set falco.syscallEventDrops.maxBurst=1000 \
            --set falco.rules.default=true \
            --set falco.rules.security=true \
            --set falco.rules.application=true \
            --set serviceMonitor.enabled=true \
            --timeout "$TIMEOUT"
    else
        log "warn" "Falco already installed."
    fi
    
    # Wait for Falco to be ready
    log "info" "Waiting for Falco to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=falco \
        -n "$SECURITY_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Falco installation completed."
}

# Install OPA Gatekeeper for policy enforcement
install_opa_gatekeeper() {
    log "info" "Installing OPA Gatekeeper for policy enforcement..."
    
    # Add Gatekeeper Helm repository
    helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
    helm repo update
    
    # Install Gatekeeper
    if ! helm list -n gatekeeper-system | grep -q "gatekeeper"; then
        kubectl create namespace gatekeeper-system --dry-run=client -o yaml | kubectl apply -f -
        
        helm install gatekeeper gatekeeper/gatekeeper \
            --namespace gatekeeper-system \
            --version "$OPA_GATEKEEPER_VERSION" \
            --set replicas=3 \
            --set auditInterval=60 \
            --set constraintViolationsLimit=20 \
            --set auditFromCache=false \
            --set emitAdmissionEvents=true \
            --set emitAuditEvents=true \
            --set logLevel=INFO \
            --set image.crdRepository=openpolicyagent/gatekeeper-crds \
            --set postInstall.labelNamespace.enabled=true \
            --set psp.enabled=false \
            --timeout "$TIMEOUT"
    else
        log "warn" "OPA Gatekeeper already installed."
    fi
    
    # Wait for Gatekeeper to be ready
    log "info" "Waiting for OPA Gatekeeper to be ready..."
    kubectl wait --for=condition=Available deployment/gatekeeper-controller-manager \
        -n gatekeeper-system --timeout="$TIMEOUT"
    kubectl wait --for=condition=Available deployment/gatekeeper-audit \
        -n gatekeeper-system --timeout="$TIMEOUT"
    
    log "info" "OPA Gatekeeper installation completed."
}

# Create basic OPA policies
create_opa_policies() {
    log "info" "Creating basic OPA security policies..."
    
    # Wait for Gatekeeper CRDs to be established
    sleep 30
    
    # Policy: Require security context
    cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiresecuritycontext
  labels:
    app.kubernetes.io/name: gatekeeper
    app.kubernetes.io/part-of: dora-compliance
spec:
  crd:
    spec:
      names:
        kind: K8sRequireSecurityContext
      validation:
        type: object
        properties:
          runAsNonRoot:
            type: boolean
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiresecuritycontext
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := "Container must run as non-root user"
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.readOnlyRootFilesystem
          msg := "Container must have read-only root filesystem"
        }
EOF

    # Apply the constraint
    cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireSecurityContext
metadata:
  name: must-have-security-context
  labels:
    app.kubernetes.io/name: gatekeeper
    app.kubernetes.io/part-of: dora-compliance
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system", "gatekeeper-system", "cert-manager"]
  parameters:
    runAsNonRoot: true
EOF

    # Policy: Disallow privileged containers
    cat <<EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8sdisallowprivileged
  labels:
    app.kubernetes.io/name: gatekeeper
    app.kubernetes.io/part-of: dora-compliance
spec:
  crd:
    spec:
      names:
        kind: K8sDisallowPrivileged
      validation:
        type: object
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sdisallowprivileged
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          container.securityContext.privileged
          msg := "Privileged containers are not allowed"
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.initContainers[_]
          container.securityContext.privileged
          msg := "Privileged init containers are not allowed"
        }
EOF

    # Apply the constraint
    cat <<EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDisallowPrivileged
metadata:
  name: disallow-privileged-containers
  labels:
    app.kubernetes.io/name: gatekeeper
    app.kubernetes.io/part-of: dora-compliance
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system", "gatekeeper-system"]
EOF
    
    log "info" "OPA security policies created successfully."
}

# Initialize Vault (manual step guidance)
initialize_vault() {
    log "info" "Vault initialization requires manual intervention..."
    log "warn" "Please run the following commands to initialize Vault:"
    echo ""
    echo "# Port forward to access Vault"
    echo "kubectl port-forward svc/vault -n $SECURITY_NAMESPACE 8200:8200 &"
    echo ""
    echo "# Set Vault address"
    echo "export VAULT_ADDR=https://127.0.0.1:8200"
    echo "export VAULT_SKIP_VERIFY=true"
    echo ""
    echo "# Initialize Vault"
    echo "vault operator init -key-shares=5 -key-threshold=3"
    echo ""
    echo "# Unseal Vault (repeat with 3 different keys)"
    echo "vault operator unseal <key1>"
    echo "vault operator unseal <key2>"
    echo "vault operator unseal <key3>"
    echo ""
    echo "# Login with root token"
    echo "vault auth <root-token>"
    echo ""
    log "warn" "Store the unseal keys and root token securely!"
}

# Verify security deployment
verify_security() {
    log "info" "Verifying security infrastructure deployment..."
    
    # Check cert-manager
    local cert_manager_pods=$(kubectl get pods -n cert-manager --no-headers | grep "Running" | wc -l)
    if [[ "$cert_manager_pods" -ge 3 ]]; then
        log "info" "✓ cert-manager is running ($cert_manager_pods pods)"
    else
        log "warn" "✗ cert-manager: only $cert_manager_pods pods running"
    fi
    
    # Check Vault
    local vault_pods=$(kubectl get pods -n "$SECURITY_NAMESPACE" -l app.kubernetes.io/name=vault --no-headers | grep "Running" | wc -l)
    if [[ "$vault_pods" -ge 3 ]]; then
        log "info" "✓ Vault cluster is running ($vault_pods pods)"
    else
        log "warn" "✗ Vault cluster: only $vault_pods pods running"
    fi
    
    # Check Falco
    local falco_pods=$(kubectl get pods -n "$SECURITY_NAMESPACE" -l app.kubernetes.io/name=falco --no-headers | grep "Running" | wc -l)
    if [[ "$falco_pods" -ge 1 ]]; then
        log "info" "✓ Falco is running ($falco_pods pods)"
    else
        log "warn" "✗ Falco is not running"
    fi
    
    # Check OPA Gatekeeper
    local gatekeeper_pods=$(kubectl get pods -n gatekeeper-system --no-headers | grep "Running" | wc -l)
    if [[ "$gatekeeper_pods" -ge 2 ]]; then
        log "info" "✓ OPA Gatekeeper is running ($gatekeeper_pods pods)"
    else
        log "warn" "✗ OPA Gatekeeper: only $gatekeeper_pods pods running"
    fi
    
    # Check network policies
    local network_policies=$(kubectl get networkpolicies --all-namespaces --no-headers | wc -l)
    if [[ "$network_policies" -ge 10 ]]; then
        log "info" "✓ Network policies applied ($network_policies policies)"
    else
        log "warn" "✗ Network policies: only $network_policies policies found"
    fi
    
    log "info" "Security infrastructure verification completed."
}

# Clean up temporary files
cleanup() {
    log "info" "Cleaning up temporary files..."
    rm -f /tmp/ca-key.pem /tmp/ca-cert.pem
}

# Main function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "info" "Starting DORA security infrastructure deployment..."
            check_prerequisites
            install_cert_manager
            create_root_ca
            install_vault
            apply_network_policies
            install_falco
            install_opa_gatekeeper
            create_opa_policies
            verify_security
            initialize_vault
            cleanup
            log "info" "Security deployment completed successfully!"
            log "warn" "Don't forget to initialize Vault manually using the provided instructions."
            ;;
        "verify")
            log "info" "Verifying security infrastructure..."
            verify_security
            ;;
        "cleanup")
            log "info" "Cleaning up temporary files..."
            cleanup
            ;;
        *)
            echo "Usage: $0 [deploy|verify|cleanup]"
            echo "  deploy: Full security infrastructure deployment (default)"
            echo "  verify: Verify security deployment status"
            echo "  cleanup: Clean up temporary files"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@" 