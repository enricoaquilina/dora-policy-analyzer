#!/bin/bash
# DORA Compliance System - Monitoring Infrastructure Setup Script

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_NAMESPACE="dora-monitoring"
TIMEOUT="600s"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"

# Component versions
PROMETHEUS_OPERATOR_VERSION="v0.68.0"
GRAFANA_VERSION="7.0.17"
ELASTICSEARCH_VERSION="8.11.0"
KIBANA_VERSION="8.11.0"
JAEGER_VERSION="1.51.0"
FLUENT_BIT_VERSION="0.21.7"

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
    log "info" "Checking monitoring setup prerequisites..."
    
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
    if ! kubectl get namespace "$MONITORING_NAMESPACE" &> /dev/null; then
        log "error" "Namespace '$MONITORING_NAMESPACE' does not exist. Please create it first."
        exit 1
    fi
    
    log "info" "All prerequisites met."
}

# Install Prometheus Operator
install_prometheus_operator() {
    log "info" "Installing Prometheus Operator..."
    
    # Add Prometheus Community Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Install kube-prometheus-stack
    if ! helm list -n "$MONITORING_NAMESPACE" | grep -q "kube-prometheus-stack"; then
        helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
            --namespace "$MONITORING_NAMESPACE" \
            --version "$PROMETHEUS_OPERATOR_VERSION" \
            --set prometheus.enabled=false \
            --set grafana.enabled=false \
            --set alertmanager.enabled=true \
            --set prometheusOperator.enabled=true \
            --set kubeStateMetrics.enabled=true \
            --set nodeExporter.enabled=true \
            --set kubeApiServer.enabled=true \
            --set kubeControllerManager.enabled=true \
            --set kubeScheduler.enabled=true \
            --set kubeEtcd.enabled=true \
            --set kubelet.enabled=true \
            --set coreDns.enabled=true \
            --set kubeDns.enabled=false \
            --set kubeProxy.enabled=true \
            --set prometheusOperator.resources.requests.cpu=100m \
            --set prometheusOperator.resources.requests.memory=128Mi \
            --set prometheusOperator.resources.limits.cpu=200m \
            --set prometheusOperator.resources.limits.memory=256Mi \
            --timeout "$TIMEOUT"
    else
        log "warn" "Prometheus Operator already installed."
    fi
    
    # Wait for Prometheus Operator to be ready
    log "info" "Waiting for Prometheus Operator to be ready..."
    kubectl wait --for=condition=Available deployment/kube-prometheus-stack-operator \
        -n "$MONITORING_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Prometheus Operator installation completed."
}

# Install custom Prometheus instance
install_prometheus() {
    log "info" "Installing custom Prometheus instance..."
    
    # Apply Prometheus configuration
    kubectl apply -f "$MONITORING_DIR/prometheus/cluster/prometheus-cluster.yaml"
    
    # Wait for Prometheus to be ready
    log "info" "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=Ready prometheus/dora-prometheus \
        -n "$MONITORING_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Prometheus installation completed."
}

# Install Grafana
install_grafana() {
    log "info" "Installing Grafana..."
    
    # Add Grafana Helm repository
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Create Grafana values file
    cat > /tmp/grafana-values.yaml << EOF
# Grafana configuration
image:
  tag: "10.2.2"

replicas: 2

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 500m
    memory: 1Gi

# Persistence
persistence:
  enabled: true
  storageClassName: dora-fast-ssd
  size: 100Gi

# Security
securityContext:
  runAsNonRoot: true
  runAsUser: 472
  fsGroup: 472

# Admin user
adminUser: admin
adminPassword: "dora-grafana-admin-password-change-me"

# Grafana configuration
grafana.ini:
  server:
    domain: grafana.dora-monitoring.svc.cluster.local
    root_url: "https://grafana.dora-monitoring.svc.cluster.local"
    serve_from_sub_path: false
  
  security:
    admin_user: admin
    admin_password: "dora-grafana-admin-password-change-me"
    secret_key: "dora-grafana-secret-key-change-me"
    disable_gravatar: true
    cookie_secure: true
    cookie_samesite: strict
    content_security_policy: true
  
  auth:
    disable_login_form: false
    disable_signout_menu: false
    oauth_auto_login: false
  
  auth.anonymous:
    enabled: false
  
  log:
    mode: console
    level: info
    format: json
  
  analytics:
    reporting_enabled: false
    check_for_updates: false
  
  snapshots:
    external_enabled: false

# Data sources
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-service.dora-monitoring.svc.cluster.local:9090
      access: proxy
      isDefault: true
      jsonData:
        timeInterval: 30s
        queryTimeout: 60s
        httpMethod: POST
    
    - name: Elasticsearch
      type: elasticsearch
      url: http://elasticsearch.dora-monitoring.svc.cluster.local:9200
      access: proxy
      database: "logstash-*"
      jsonData:
        esVersion: "8.0.0"
        timeField: "@timestamp"
        interval: Daily
        maxConcurrentShardRequests: 5
    
    - name: Jaeger
      type: jaeger
      url: http://jaeger-query.dora-monitoring.svc.cluster.local:16686
      access: proxy

# Dashboard providers
dashboardProviders:
  dashboardproviders.yaml:
    apiVersion: 1
    providers:
    - name: 'infrastructure'
      orgId: 1
      folder: 'Infrastructure'
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      allowUiUpdates: true
      options:
        path: /var/lib/grafana/dashboards/infrastructure
    
    - name: 'applications'
      orgId: 1
      folder: 'Applications'
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      allowUiUpdates: true
      options:
        path: /var/lib/grafana/dashboards/applications
    
    - name: 'security'
      orgId: 1
      folder: 'Security'
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      allowUiUpdates: true
      options:
        path: /var/lib/grafana/dashboards/security
    
    - name: 'compliance'
      orgId: 1
      folder: 'Compliance'
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      allowUiUpdates: true
      options:
        path: /var/lib/grafana/dashboards/compliance

# Service configuration
service:
  type: ClusterIP
  port: 80
  targetPort: 3000

# Node placement
nodeSelector:
  role: monitoring

tolerations:
- key: "monitoring"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"

# Pod anti-affinity
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app.kubernetes.io/name: grafana
      topologyKey: kubernetes.io/hostname

# ServiceMonitor
serviceMonitor:
  enabled: true
  labels:
    app.kubernetes.io/part-of: dora-compliance
EOF
    
    # Install Grafana
    if ! helm list -n "$MONITORING_NAMESPACE" | grep -q "grafana"; then
        helm install grafana grafana/grafana \
            --namespace "$MONITORING_NAMESPACE" \
            --values /tmp/grafana-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "Grafana already installed."
    fi
    
    # Wait for Grafana to be ready
    log "info" "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=grafana \
        -n "$MONITORING_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Grafana installation completed."
}

# Install Elasticsearch
install_elasticsearch() {
    log "info" "Installing Elasticsearch..."
    
    # Add Elastic Helm repository
    helm repo add elastic https://helm.elastic.co
    helm repo update
    
    # Create Elasticsearch values file
    cat > /tmp/elasticsearch-values.yaml << EOF
# Elasticsearch configuration
image: "docker.elastic.co/elasticsearch/elasticsearch"
imageTag: "$ELASTICSEARCH_VERSION"

clusterName: "dora-elasticsearch"
nodeGroup: "master"

# Cluster topology
master:
  enabled: true
  replicas: 3
  heapSize: "2g"

data:
  enabled: true
  replicas: 3
  heapSize: "4g"

coordinating:
  enabled: true
  replicas: 2
  heapSize: "1g"

# Resource allocation
resources:
  requests:
    cpu: "1"
    memory: "4Gi"
  limits:
    cpu: "2"
    memory: "8Gi"

# Volume configuration
volumeClaimTemplate:
  accessModes: ["ReadWriteOnce"]
  storageClassName: dora-fast-ssd
  resources:
    requests:
      storage: 2Ti

# Elasticsearch configuration
esConfig:
  elasticsearch.yml: |
    cluster.name: dora-elasticsearch
    discovery.type: zen
    network.host: 0.0.0.0
    
    # Security
    xpack.security.enabled: true
    xpack.security.transport.ssl.enabled: true
    xpack.security.transport.ssl.verification_mode: certificate
    xpack.security.http.ssl.enabled: true
    
    # Index management
    action.auto_create_index: false
    indices.recovery.max_bytes_per_sec: 100mb
    
    # Performance tuning
    bootstrap.memory_lock: true
    thread_pool.write.queue_size: 1000
    thread_pool.search.queue_size: 1000
    
    # Logging
    logger.org.elasticsearch.discovery: DEBUG

# Environment variables
extraEnvs:
- name: ES_JAVA_OPTS
  value: "-Xms4g -Xmx4g -XX:+UseG1GC"
- name: discovery.seed_hosts
  value: "dora-elasticsearch-master-0.dora-elasticsearch-master-headless.dora-monitoring.svc.cluster.local,dora-elasticsearch-master-1.dora-elasticsearch-master-headless.dora-monitoring.svc.cluster.local,dora-elasticsearch-master-2.dora-elasticsearch-master-headless.dora-monitoring.svc.cluster.local"
- name: cluster.initial_master_nodes
  value: "dora-elasticsearch-master-0,dora-elasticsearch-master-1,dora-elasticsearch-master-2"

# Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

# Node placement
nodeSelector:
  role: data

tolerations:
- key: "data"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"

# Pod anti-affinity
antiAffinity: "hard"
EOF
    
    # Install Elasticsearch
    if ! helm list -n "$MONITORING_NAMESPACE" | grep -q "elasticsearch"; then
        helm install elasticsearch elastic/elasticsearch \
            --namespace "$MONITORING_NAMESPACE" \
            --values /tmp/elasticsearch-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "Elasticsearch already installed."
    fi
    
    # Wait for Elasticsearch to be ready
    log "info" "Waiting for Elasticsearch to be ready..."
    kubectl wait --for=condition=Ready pod -l app=elasticsearch-master \
        -n "$MONITORING_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Elasticsearch installation completed."
}

# Install Fluent Bit
install_fluent_bit() {
    log "info" "Installing Fluent Bit..."
    
    # Add Fluent Bit Helm repository
    helm repo add fluent https://fluent.github.io/helm-charts
    helm repo update
    
    # Create Fluent Bit values file
    cat > /tmp/fluent-bit-values.yaml << EOF
# Fluent Bit configuration
image:
  repository: fluent/fluent-bit
  tag: "$FLUENT_BIT_VERSION"

# DaemonSet configuration
kind: DaemonSet

# Resource allocation
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi

# Configuration
config:
  service: |
    [SERVICE]
        Daemon Off
        Flush 1
        Log_Level info
        Parsers_File parsers.conf
        Parsers_File custom_parsers.conf
        HTTP_Server On
        HTTP_Listen 0.0.0.0
        HTTP_Port 2020
        Health_Check On
        storage.path /tmp/flb-storage/
        storage.sync normal
        storage.checksum off
        storage.backlog.mem_limit 50M

  inputs: |
    [INPUT]
        Name tail
        Path /var/log/containers/*.log
        multiline.parser docker, cri
        Tag kube.*
        Mem_Buf_Limit 50MB
        Skip_Long_Lines On
        storage.type filesystem
        
    [INPUT]
        Name systemd
        Tag host.*
        Systemd_Filter _SYSTEMD_UNIT=kubelet.service
        Read_From_Head On

  filters: |
    [FILTER]
        Name kubernetes
        Match kube.*
        Kube_URL https://kubernetes.default.svc:443
        Kube_CA_File /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File /var/run/secrets/kubernetes.io/serviceaccount/token
        Kube_Tag_Prefix kube.var.log.containers.
        Merge_Log On
        Keep_Log Off
        K8S-Logging.Parser On
        K8S-Logging.Exclude Off
        Annotations Off
        Labels On
        
    [FILTER]
        Name modify
        Match kube.*
        Add cluster dora-main
        Add environment production

  outputs: |
    [OUTPUT]
        Name es
        Match kube.*
        Host elasticsearch.dora-monitoring.svc.cluster.local
        Port 9200
        Logstash_Format On
        Logstash_Prefix app-logs
        Logstash_DateFormat %Y.%m.%d
        Include_Tag_Key On
        Tag_Key tag
        Time_Key @timestamp
        Replace_Dots On
        Retry_Limit 3
        storage.total_limit_size 1G
        
    [OUTPUT]
        Name es
        Match host.*
        Host elasticsearch.dora-monitoring.svc.cluster.local
        Port 9200
        Logstash_Format On
        Logstash_Prefix infra-logs
        Logstash_DateFormat %Y.%m.%d
        Include_Tag_Key On
        Tag_Key tag
        Time_Key @timestamp
        Retry_Limit 3
        storage.total_limit_size 1G

  customParsers: |
    [PARSER]
        Name docker_no_time
        Format json
        Time_Keep Off
        Time_Key time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        
    [PARSER]
        Name dora_compliance
        Format regex
        Regex ^(?<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\s+(?<level>\w+)\s+\[(?<service>[^\]]+)\]\s+(?<message>.*)$
        Time_Key timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%L

# Node placement
nodeSelector:
  kubernetes.io/os: linux

tolerations:
- operator: Exists
  effect: NoSchedule
- operator: Exists
  effect: NoExecute

# ServiceMonitor
serviceMonitor:
  enabled: true
  labels:
    app.kubernetes.io/part-of: dora-compliance
EOF
    
    # Install Fluent Bit
    if ! helm list -n "$MONITORING_NAMESPACE" | grep -q "fluent-bit"; then
        helm install fluent-bit fluent/fluent-bit \
            --namespace "$MONITORING_NAMESPACE" \
            --values /tmp/fluent-bit-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "Fluent Bit already installed."
    fi
    
    # Wait for Fluent Bit to be ready
    log "info" "Waiting for Fluent Bit to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=fluent-bit \
        -n "$MONITORING_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Fluent Bit installation completed."
}

# Install Jaeger
install_jaeger() {
    log "info" "Installing Jaeger..."
    
    # Add Jaeger Helm repository
    helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
    helm repo update
    
    # Create Jaeger values file
    cat > /tmp/jaeger-values.yaml << EOF
# Jaeger configuration
strategy: production

provisionDataStore:
  elasticsearch: true

elasticsearch:
  host: elasticsearch.dora-monitoring.svc.cluster.local
  port: 9200

collector:
  enabled: true
  replicaCount: 3
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi

query:
  enabled: true
  replicaCount: 2
  resources:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 500m
      memory: 1Gi

agent:
  enabled: true
  daemonset:
    useHostPort: true

# Node placement
nodeSelector:
  role: monitoring

tolerations:
- key: "monitoring"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
EOF
    
    # Install Jaeger
    if ! helm list -n "$MONITORING_NAMESPACE" | grep -q "jaeger"; then
        helm install jaeger jaegertracing/jaeger \
            --namespace "$MONITORING_NAMESPACE" \
            --values /tmp/jaeger-values.yaml \
            --timeout "$TIMEOUT"
    else
        log "warn" "Jaeger already installed."
    fi
    
    # Wait for Jaeger to be ready
    log "info" "Waiting for Jaeger to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=query \
        -n "$MONITORING_NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Jaeger installation completed."
}

# Create custom dashboards
create_dashboards() {
    log "info" "Creating custom Grafana dashboards..."
    
    # Create infrastructure dashboard ConfigMap
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: infrastructure-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: grafana
    app.kubernetes.io/part-of: dora-compliance
    grafana_dashboard: "1"
data:
  infrastructure-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "DORA Infrastructure Overview",
        "tags": ["infrastructure", "kubernetes", "dora"],
        "style": "dark",
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Cluster Overview",
            "type": "stat",
            "targets": [
              {
                "expr": "count(kube_node_info)",
                "legendFormat": "Total Nodes"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
EOF
    
    log "info" "Custom dashboards created."
}

# Verify monitoring deployment
verify_monitoring() {
    log "info" "Verifying monitoring infrastructure deployment..."
    
    # Check Prometheus Operator
    local prometheus_op_pods=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app.kubernetes.io/name=kube-prometheus-stack-operator --no-headers | grep "Running" | wc -l)
    if [[ "$prometheus_op_pods" -ge 1 ]]; then
        log "info" "✓ Prometheus Operator is running"
    else
        log "warn" "✗ Prometheus Operator is not running"
    fi
    
    # Check Prometheus
    local prometheus_pods=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app.kubernetes.io/name=prometheus --no-headers | grep "Running" | wc -l)
    if [[ "$prometheus_pods" -ge 3 ]]; then
        log "info" "✓ Prometheus cluster is running ($prometheus_pods pods)"
    else
        log "warn" "✗ Prometheus cluster: only $prometheus_pods pods running"
    fi
    
    # Check Grafana
    local grafana_pods=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app.kubernetes.io/name=grafana --no-headers | grep "Running" | wc -l)
    if [[ "$grafana_pods" -ge 2 ]]; then
        log "info" "✓ Grafana is running ($grafana_pods pods)"
    else
        log "warn" "✗ Grafana: only $grafana_pods pods running"
    fi
    
    # Check Elasticsearch
    local elasticsearch_pods=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app=elasticsearch-master --no-headers | grep "Running" | wc -l)
    if [[ "$elasticsearch_pods" -ge 3 ]]; then
        log "info" "✓ Elasticsearch cluster is running ($elasticsearch_pods pods)"
    else
        log "warn" "✗ Elasticsearch cluster: only $elasticsearch_pods pods running"
    fi
    
    # Check Fluent Bit
    local fluent_bit_pods=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app.kubernetes.io/name=fluent-bit --no-headers | grep "Running" | wc -l)
    if [[ "$fluent_bit_pods" -ge 1 ]]; then
        log "info" "✓ Fluent Bit is running ($fluent_bit_pods pods)"
    else
        log "warn" "✗ Fluent Bit is not running"
    fi
    
    # Check Jaeger
    local jaeger_pods=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app.kubernetes.io/component=query --no-headers | grep "Running" | wc -l)
    if [[ "$jaeger_pods" -ge 2 ]]; then
        log "info" "✓ Jaeger is running ($jaeger_pods pods)"
    else
        log "warn" "✗ Jaeger: only $jaeger_pods pods running"
    fi
    
    # Display access information
    log "info" "Monitoring services access information:"
    echo "  Prometheus: http://prometheus-service.$MONITORING_NAMESPACE.svc.cluster.local:9090"
    echo "  Grafana: http://grafana.$MONITORING_NAMESPACE.svc.cluster.local"
    echo "  Elasticsearch: http://elasticsearch.$MONITORING_NAMESPACE.svc.cluster.local:9200"
    echo "  Jaeger: http://jaeger-query.$MONITORING_NAMESPACE.svc.cluster.local:16686"
    echo "  AlertManager: http://alertmanager-main.$MONITORING_NAMESPACE.svc.cluster.local:9093"
    
    log "info" "Monitoring infrastructure verification completed."
}

# Clean up temporary files
cleanup() {
    log "info" "Cleaning up temporary files..."
    rm -f /tmp/grafana-values.yaml /tmp/elasticsearch-values.yaml /tmp/fluent-bit-values.yaml /tmp/jaeger-values.yaml
}

# Main function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "info" "Starting DORA monitoring infrastructure deployment..."
            check_prerequisites
            install_prometheus_operator
            install_prometheus
            install_grafana
            install_elasticsearch
            install_fluent_bit
            install_jaeger
            create_dashboards
            verify_monitoring
            cleanup
            log "info" "Monitoring deployment completed successfully!"
            ;;
        "verify")
            log "info" "Verifying monitoring infrastructure..."
            verify_monitoring
            ;;
        "cleanup")
            log "info" "Cleaning up temporary files..."
            cleanup
            ;;
        *)
            echo "Usage: $0 [deploy|verify|cleanup]"
            echo "  deploy: Full monitoring infrastructure deployment (default)"
            echo "  verify: Verify monitoring deployment status"
            echo "  cleanup: Clean up temporary files"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@" 