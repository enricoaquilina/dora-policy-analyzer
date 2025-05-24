#!/bin/bash
# DORA Compliance System - Database Setup Script

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="dora-data"
TIMEOUT="600s"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATABASE_DIR="$(dirname "$SCRIPT_DIR")"

# Database versions
POSTGRESQL_OPERATOR_VERSION="1.10.1"
REDIS_OPERATOR_VERSION="1.2.4"
NEO4J_VERSION="5.15.0"
MONGODB_VERSION="7.0.4"
INFLUXDB_VERSION="2.7.5"

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
    log "info" "Checking prerequisites..."
    
    # Check for required tools
    local required_tools=("kubectl" "helm")
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
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "error" "Namespace '$NAMESPACE' does not exist. Please create it first."
        exit 1
    fi
    
    log "info" "All prerequisites met."
}

# Install PostgreSQL using CloudNativePG operator
install_postgresql() {
    log "info" "Installing PostgreSQL with CloudNativePG operator..."
    
    # Add CloudNativePG Helm repository
    helm repo add cnpg https://cloudnative-pg.github.io/charts
    helm repo update
    
    # Install CloudNativePG operator
    if ! helm list -n cnpg-system | grep -q "cloudnative-pg"; then
        kubectl create namespace cnpg-system --dry-run=client -o yaml | kubectl apply -f -
        
        helm install cloudnative-pg cnpg/cloudnative-pg \
            --namespace cnpg-system \
            --version "$POSTGRESQL_OPERATOR_VERSION" \
            --create-namespace \
            --timeout "$TIMEOUT"
    else
        log "warn" "CloudNativePG operator already installed."
    fi
    
    # Wait for operator to be ready
    log "info" "Waiting for CloudNativePG operator to be ready..."
    kubectl wait --for=condition=Available deployment/cnpg-controller-manager \
        -n cnpg-system --timeout="$TIMEOUT"
    
    # Deploy PostgreSQL cluster
    log "info" "Deploying PostgreSQL cluster..."
    kubectl apply -f "$DATABASE_DIR/postgresql/cluster/postgresql-cluster.yaml"
    
    # Wait for PostgreSQL cluster to be ready
    log "info" "Waiting for PostgreSQL cluster to be ready..."
    kubectl wait --for=condition=Ready cluster/dora-postgresql-cluster \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    # Apply schema
    log "info" "Applying PostgreSQL schema..."
    kubectl run postgres-schema-init --image=postgres:16 \
        --rm -it --restart=Never \
        --namespace="$NAMESPACE" \
        --env="PGPASSWORD=$(kubectl get secret dora-postgresql-app-user -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d)" \
        --command -- psql \
        -h dora-postgresql-cluster-rw \
        -U dora_app \
        -d dora_compliance \
        -f /tmp/schema.sql \
        --quiet || log "warn" "Schema application may have failed - check manually"
    
    log "info" "PostgreSQL installation completed."
}

# Install Redis using Redis Operator
install_redis() {
    log "info" "Installing Redis with Redis Operator..."
    
    # Add Redis Operator Helm repository
    helm repo add redis-operator https://spotahome.github.io/redis-operator
    helm repo update
    
    # Install Redis Operator
    if ! helm list -n redis-operator | grep -q "redis-operator"; then
        kubectl create namespace redis-operator --dry-run=client -o yaml | kubectl apply -f -
        
        helm install redis-operator redis-operator/redis-operator \
            --namespace redis-operator \
            --version "$REDIS_OPERATOR_VERSION" \
            --create-namespace \
            --timeout "$TIMEOUT"
    else
        log "warn" "Redis operator already installed."
    fi
    
    # Wait for operator to be ready
    log "info" "Waiting for Redis operator to be ready..."
    kubectl wait --for=condition=Available deployment/redis-operator \
        -n redis-operator --timeout="$TIMEOUT"
    
    # Deploy Redis cluster
    log "info" "Deploying Redis cluster..."
    kubectl apply -f "$DATABASE_DIR/redis/cluster/redis-cluster.yaml"
    
    # Wait for Redis cluster to be ready
    log "info" "Waiting for Redis cluster to be ready..."
    sleep 60  # Give Redis time to initialize
    
    log "info" "Redis installation completed."
}

# Install Neo4j
install_neo4j() {
    log "info" "Installing Neo4j..."
    
    # Add Neo4j Helm repository
    helm repo add neo4j https://helm.neo4j.com/neo4j
    helm repo update
    
    # Create Neo4j values file
    cat > /tmp/neo4j-values.yaml << EOF
neo4j:
  name: "dora-neo4j"
  edition: "community"
  acceptLicenseAgreement: "yes"
  
  # Password configuration
  password: "dora-neo4j-secure-password-change-me"
  
  # Resource configuration
  resources:
    cpu: "1000m"
    memory: "4Gi"
  
  # Storage configuration
  volumes:
    data:
      mode: "defaultStorageClass"
      defaultStorageClass:
        storageClassName: "dora-fast-ssd"
        requests:
          storage: "200Gi"
    logs:
      mode: "defaultStorageClass"
      defaultStorageClass:
        storageClassName: "dora-standard-ssd"
        requests:
          storage: "20Gi"
  
  # Security configuration
  ssl:
    bolt:
      enabled: true
      generateCert: true
    https:
      enabled: true
      generateCert: true
  
  # Database configuration
  config:
    dbms.memory.heap.initial_size: "2G"
    dbms.memory.heap.max_size: "3G"
    dbms.memory.pagecache.size: "1G"
    dbms.security.auth_enabled: "true"
    dbms.logs.query.enabled: "INFO"
    dbms.logs.query.threshold: "1s"
    dbms.connector.bolt.listen_address: "0.0.0.0:7687"
    dbms.connector.http.listen_address: "0.0.0.0:7474"
    dbms.connector.https.listen_address: "0.0.0.0:7473"
    
  # Node placement
  nodeSelector:
    role: data
  
  tolerations:
    - key: "data"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"

# Service configuration
service:
  type: ClusterIP
  
# Monitoring
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
EOF
    
    # Install Neo4j
    if ! helm list -n "$NAMESPACE" | grep -q "neo4j"; then
        helm install neo4j neo4j/neo4j \
            --namespace "$NAMESPACE" \
            --values /tmp/neo4j-values.yaml \
            --version "$NEO4J_VERSION" \
            --timeout "$TIMEOUT"
    else
        log "warn" "Neo4j already installed."
    fi
    
    # Wait for Neo4j to be ready
    log "info" "Waiting for Neo4j to be ready..."
    kubectl wait --for=condition=Ready pod -l app=neo4j \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Neo4j installation completed."
}

# Install MongoDB
install_mongodb() {
    log "info" "Installing MongoDB..."
    
    # Add MongoDB Helm repository
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    
    # Create MongoDB values file
    cat > /tmp/mongodb-values.yaml << EOF
architecture: replicaset
replicaCount: 3

auth:
  enabled: true
  rootUser: "root"
  rootPassword: "dora-mongodb-root-password-change-me"
  username: "dora_app"
  password: "dora-mongodb-app-password-change-me"
  database: "dora_compliance"

persistence:
  enabled: true
  storageClass: "dora-fast-ssd"
  size: "300Gi"

resources:
  requests:
    cpu: "500m"
    memory: "2Gi"
  limits:
    cpu: "1"
    memory: "4Gi"

nodeSelector:
  role: data

tolerations:
  - key: "data"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"

podAntiAffinityPreset: hard

metrics:
  enabled: true
  serviceMonitor:
    enabled: true

arbiter:
  enabled: true
  nodeSelector:
    role: data
  tolerations:
    - key: "data"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"

configurationConfigMap: mongodb-config
EOF
    
    # Create MongoDB configuration
    kubectl apply -f - << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: mongodb-config
  namespace: $NAMESPACE
data:
  mongod.conf: |
    net:
      port: 27017
      bindIp: 0.0.0.0
      tls:
        mode: requireTLS
        certificateKeyFile: /etc/ssl/mongodb.pem
        CAFile: /etc/ssl/ca.pem
    
    security:
      authorization: enabled
      clusterAuthMode: x509
    
    replication:
      replSetName: rs0
    
    storage:
      engine: wiredTiger
      wiredTiger:
        engineConfig:
          cacheSizeGB: 2
          journalCompressor: snappy
          directoryForIndexes: true
        collectionConfig:
          blockCompressor: snappy
        indexConfig:
          prefixCompression: true
    
    operationProfiling:
      mode: slowOp
      slowOpThresholdMs: 1000
    
    setParameter:
      logLevel: 1
      enableLocalhostAuthBypass: false
EOF
    
    # Install MongoDB
    if ! helm list -n "$NAMESPACE" | grep -q "mongodb"; then
        helm install mongodb bitnami/mongodb \
            --namespace "$NAMESPACE" \
            --values /tmp/mongodb-values.yaml \
            --version "$MONGODB_VERSION" \
            --timeout "$TIMEOUT"
    else
        log "warn" "MongoDB already installed."
    fi
    
    # Wait for MongoDB to be ready
    log "info" "Waiting for MongoDB to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=mongodb \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "MongoDB installation completed."
}

# Install InfluxDB
install_influxdb() {
    log "info" "Installing InfluxDB..."
    
    # Add InfluxDB Helm repository
    helm repo add influxdata https://helm.influxdata.com/
    helm repo update
    
    # Create InfluxDB values file
    cat > /tmp/influxdb-values.yaml << EOF
image:
  tag: "$INFLUXDB_VERSION"

adminUser:
  organization: "dora-compliance"
  bucket: "dora-metrics"
  user: "admin"
  password: "dora-influxdb-admin-password-change-me"
  token: "dora-influxdb-admin-token-change-me"

persistence:
  enabled: true
  storageClass: "dora-fast-ssd"
  size: "500Gi"

resources:
  requests:
    cpu: "500m"
    memory: "2Gi"
  limits:
    cpu: "2"
    memory: "8Gi"

nodeSelector:
  role: data

tolerations:
  - key: "data"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"

service:
  type: ClusterIP
  port: 8086

ingress:
  enabled: false

env:
  - name: INFLUXDB_HTTP_AUTH_ENABLED
    value: "true"
  - name: INFLUXDB_HTTP_FLUX_ENABLED
    value: "true"
  - name: INFLUXDB_LOGGING_LEVEL
    value: "info"

configMap:
  config.toml: |
    [http]
      bind-address = ":8086"
      auth-enabled = true
      log-enabled = true
      write-tracing = false
      pprof-enabled = true
      debug-pprof-enabled = false
      https-enabled = false
    
    [logging]
      format = "auto"
      level = "info"
      suppress-logo = false
    
    [continuous_queries]
      enabled = true
      log-enabled = true
      query-stats-enabled = false
      run-interval = "1s"
EOF
    
    # Install InfluxDB
    if ! helm list -n "$NAMESPACE" | grep -q "influxdb"; then
        helm install influxdb influxdata/influxdb2 \
            --namespace "$NAMESPACE" \
            --values /tmp/influxdb-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "InfluxDB already installed."
    fi
    
    # Wait for InfluxDB to be ready
    log "info" "Waiting for InfluxDB to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=influxdb2 \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "InfluxDB installation completed."
}

# Verify all database deployments
verify_databases() {
    log "info" "Verifying database deployments..."
    
    # Check PostgreSQL
    local pg_status=$(kubectl get cluster dora-postgresql-cluster -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    if [[ "$pg_status" == "Cluster in healthy state" ]]; then
        log "info" "✓ PostgreSQL cluster is healthy"
    else
        log "warn" "✗ PostgreSQL cluster status: $pg_status"
    fi
    
    # Check Redis
    local redis_pods=$(kubectl get pods -l app.kubernetes.io/name=redis -n "$NAMESPACE" --no-headers | grep "Running" | wc -l)
    if [[ "$redis_pods" -ge 3 ]]; then
        log "info" "✓ Redis cluster is running ($redis_pods pods)"
    else
        log "warn" "✗ Redis cluster: only $redis_pods pods running"
    fi
    
    # Check Neo4j
    local neo4j_pods=$(kubectl get pods -l app=neo4j -n "$NAMESPACE" --no-headers | grep "Running" | wc -l)
    if [[ "$neo4j_pods" -ge 1 ]]; then
        log "info" "✓ Neo4j is running"
    else
        log "warn" "✗ Neo4j is not running"
    fi
    
    # Check MongoDB
    local mongodb_pods=$(kubectl get pods -l app.kubernetes.io/name=mongodb -n "$NAMESPACE" --no-headers | grep "Running" | wc -l)
    if [[ "$mongodb_pods" -ge 3 ]]; then
        log "info" "✓ MongoDB replica set is running ($mongodb_pods pods)"
    else
        log "warn" "✗ MongoDB replica set: only $mongodb_pods pods running"
    fi
    
    # Check InfluxDB
    local influxdb_pods=$(kubectl get pods -l app.kubernetes.io/name=influxdb2 -n "$NAMESPACE" --no-headers | grep "Running" | wc -l)
    if [[ "$influxdb_pods" -ge 1 ]]; then
        log "info" "✓ InfluxDB is running"
    else
        log "warn" "✗ InfluxDB is not running"
    fi
    
    # Display connection information
    log "info" "Database connection information:"
    echo "  PostgreSQL:"
    echo "    Primary: postgresql-primary.$NAMESPACE.svc.cluster.local:5432"
    echo "    Read-only: postgresql-readonly.$NAMESPACE.svc.cluster.local:5432"
    echo "    Database: dora_compliance"
    echo "    User: dora_app"
    echo ""
    echo "  Redis:"
    echo "    Master: redis-master.$NAMESPACE.svc.cluster.local:6379"
    echo "    Sentinel: redis-sentinel.$NAMESPACE.svc.cluster.local:26379"
    echo ""
    echo "  Neo4j:"
    echo "    Bolt: neo4j.$NAMESPACE.svc.cluster.local:7687"
    echo "    HTTP: neo4j.$NAMESPACE.svc.cluster.local:7474"
    echo ""
    echo "  MongoDB:"
    echo "    URI: mongodb://mongodb-0.$NAMESPACE.svc.cluster.local:27017,mongodb-1.$NAMESPACE.svc.cluster.local:27017,mongodb-2.$NAMESPACE.svc.cluster.local:27017/dora_compliance?replicaSet=rs0"
    echo ""
    echo "  InfluxDB:"
    echo "    HTTP: influxdb.$NAMESPACE.svc.cluster.local:8086"
    echo "    Organization: dora-compliance"
    echo "    Bucket: dora-metrics"
}

# Clean up temporary files
cleanup() {
    log "info" "Cleaning up temporary files..."
    rm -f /tmp/neo4j-values.yaml /tmp/mongodb-values.yaml /tmp/influxdb-values.yaml
}

# Main function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "info" "Starting DORA database infrastructure deployment..."
            check_prerequisites
            install_postgresql
            install_redis
            install_neo4j
            install_mongodb
            install_influxdb
            verify_databases
            cleanup
            log "info" "Database deployment completed successfully!"
            ;;
        "verify")
            log "info" "Verifying database deployments..."
            verify_databases
            ;;
        "cleanup")
            log "info" "Cleaning up temporary files..."
            cleanup
            ;;
        *)
            echo "Usage: $0 [deploy|verify|cleanup]"
            echo "  deploy: Full database infrastructure deployment (default)"
            echo "  verify: Verify deployment status"
            echo "  cleanup: Clean up temporary files"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@" 