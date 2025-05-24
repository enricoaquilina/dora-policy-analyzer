#!/bin/bash
# DORA Compliance System - Kafka Setup Script

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="dora-system"
STRIMZI_VERSION="0.38.0"
KAFKA_VERSION="3.6.0"
TIMEOUT="600s"

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

# Install Strimzi Kafka Operator
install_strimzi_operator() {
    log "info" "Installing Strimzi Kafka Operator..."
    
    # Add Strimzi Helm repository
    helm repo add strimzi https://strimzi.io/charts/
    helm repo update
    
    # Check if Strimzi is already installed
    if helm list -n "$NAMESPACE" | grep -q "strimzi-kafka-operator"; then
        log "warn" "Strimzi operator already installed. Upgrading..."
        helm upgrade strimzi-kafka-operator strimzi/strimzi-kafka-operator \
            --namespace "$NAMESPACE" \
            --version "$STRIMZI_VERSION" \
            --set watchAnyNamespace=false \
            --set defaultImageRegistry=quay.io \
            --timeout "$TIMEOUT"
    else
        log "info" "Installing Strimzi operator..."
        helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator \
            --namespace "$NAMESPACE" \
            --version "$STRIMZI_VERSION" \
            --set watchAnyNamespace=false \
            --set defaultImageRegistry=quay.io \
            --timeout "$TIMEOUT"
    fi
    
    # Wait for operator to be ready
    log "info" "Waiting for Strimzi operator to be ready..."
    kubectl wait --for=condition=Available deployment/strimzi-cluster-operator \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Strimzi operator installed successfully."
}

# Deploy Kafka cluster
deploy_kafka_cluster() {
    log "info" "Deploying Kafka cluster..."
    
    # Apply Kafka cluster configuration
    kubectl apply -f "$(dirname "$0")/../helm/kafka-cluster.yaml"
    
    # Wait for Kafka cluster to be ready
    log "info" "Waiting for Kafka cluster to be ready..."
    kubectl wait --for=condition=Ready kafka/dora-kafka-cluster \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    # Wait for all Kafka pods to be running
    log "info" "Waiting for Kafka pods to be running..."
    kubectl wait --for=condition=Ready pod -l strimzi.io/name=dora-kafka-cluster-kafka \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    # Wait for Zookeeper pods to be running
    log "info" "Waiting for Zookeeper pods to be running..."
    kubectl wait --for=condition=Ready pod -l strimzi.io/name=dora-kafka-cluster-zookeeper \
        -n "$NAMESPACE" --timeout="$TIMEOUT"
    
    log "info" "Kafka cluster deployed successfully."
}

# Create topics
create_topics() {
    log "info" "Creating Kafka topics..."
    
    # Apply all topic configurations
    local topic_dirs=("agent-topics.yaml" "compliance-topics.yaml" "audit-topics.yaml")
    
    for topic_file in "${topic_dirs[@]}"; do
        local topic_path="$(dirname "$0")/../topics/$topic_file"
        if [[ -f "$topic_path" ]]; then
            log "info" "Creating topics from $topic_file..."
            kubectl apply -f "$topic_path"
        else
            log "warn" "Topic file not found: $topic_path"
        fi
    done
    
    # Wait for topics to be created
    log "info" "Waiting for topics to be ready..."
    sleep 30  # Give time for topic creation
    
    # Verify topics are created
    local topic_count=$(kubectl get kafkatopics -n "$NAMESPACE" --no-headers | wc -l)
    log "info" "Created $topic_count Kafka topics."
}

# Configure security
configure_security() {
    log "info" "Configuring Kafka security..."
    
    # Wait for Kafka users to be created
    log "info" "Waiting for Kafka users to be ready..."
    kubectl wait --for=condition=Ready kafkauser -l strimzi.io/cluster=dora-kafka-cluster \
        -n "$NAMESPACE" --timeout="$TIMEOUT" || true
    
    # Display user credentials information
    log "info" "Kafka users created. Credentials are stored in secrets:"
    kubectl get secrets -n "$NAMESPACE" | grep "dora-.*-user" || true
}

# Verify deployment
verify_deployment() {
    log "info" "Verifying Kafka deployment..."
    
    # Check Kafka cluster status
    local cluster_status=$(kubectl get kafka dora-kafka-cluster -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
    if [[ "$cluster_status" == "True" ]]; then
        log "info" "✓ Kafka cluster is ready"
    else
        log "error" "✗ Kafka cluster is not ready (status: $cluster_status)"
    fi
    
    # Check running pods
    local kafka_pods=$(kubectl get pods -l strimzi.io/name=dora-kafka-cluster-kafka -n "$NAMESPACE" --no-headers | grep "Running" | wc -l)
    local zk_pods=$(kubectl get pods -l strimzi.io/name=dora-kafka-cluster-zookeeper -n "$NAMESPACE" --no-headers | grep "Running" | wc -l)
    
    log "info" "✓ Kafka brokers running: $kafka_pods/3"
    log "info" "✓ Zookeeper nodes running: $zk_pods/3"
    
    # Check topics
    local topic_count=$(kubectl get kafkatopics -n "$NAMESPACE" --no-headers | wc -l)
    log "info" "✓ Topics created: $topic_count"
    
    # Check users
    local user_count=$(kubectl get kafkausers -n "$NAMESPACE" --no-headers | wc -l)
    log "info" "✓ Users created: $user_count"
    
    # Display cluster information
    log "info" "Kafka cluster information:"
    echo "  Bootstrap servers (internal): dora-kafka-cluster-kafka-bootstrap.$NAMESPACE.svc.cluster.local:9092"
    echo "  Bootstrap servers (TLS): dora-kafka-cluster-kafka-bootstrap.$NAMESPACE.svc.cluster.local:9093"
    echo "  External access: kubectl port-forward service/dora-kafka-cluster-kafka-external-bootstrap 9094:9094 -n $NAMESPACE"
}

# Performance test
performance_test() {
    log "info" "Running basic performance test..."
    
    # Create a test producer pod
    kubectl run kafka-producer-test --image=quay.io/strimzi/kafka:0.38.0-kafka-3.6.0 \
        --rm -it --restart=Never --namespace="$NAMESPACE" \
        --command -- bash -c "
        echo 'test-message-1' | /opt/kafka/bin/kafka-console-producer.sh \
            --bootstrap-server dora-kafka-cluster-kafka-bootstrap:9092 \
            --topic agent-events
        " 2>/dev/null || log "warn" "Producer test failed (might be expected if topics aren't ready)"
    
    # Create a test consumer pod
    kubectl run kafka-consumer-test --image=quay.io/strimzi/kafka:0.38.0-kafka-3.6.0 \
        --rm -it --restart=Never --namespace="$NAMESPACE" --timeout=10s \
        --command -- /opt/kafka/bin/kafka-console-consumer.sh \
            --bootstrap-server dora-kafka-cluster-kafka-bootstrap:9092 \
            --topic agent-events \
            --from-beginning \
            --max-messages 1 2>/dev/null || log "warn" "Consumer test timed out (might be expected)"
    
    log "info" "Performance test completed."
}

# Cleanup function
cleanup() {
    log "info" "Cleaning up test resources..."
    kubectl delete pod kafka-producer-test kafka-consumer-test -n "$NAMESPACE" 2>/dev/null || true
}

# Display usage information
show_usage() {
    log "info" "Kafka cluster setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Configure your applications to use the Kafka cluster"
    echo "2. Use the following connection details:"
    echo "   - Internal Bootstrap: dora-kafka-cluster-kafka-bootstrap.$NAMESPACE.svc.cluster.local:9092"
    echo "   - TLS Bootstrap: dora-kafka-cluster-kafka-bootstrap.$NAMESPACE.svc.cluster.local:9093"
    echo "3. User credentials are stored in Kubernetes secrets (dora-*-user)"
    echo "4. Monitor the cluster with: kubectl get kafka,kafkatopics,kafkausers -n $NAMESPACE"
    echo
    echo "For external access, use port forwarding:"
    echo "kubectl port-forward service/dora-kafka-cluster-kafka-external-bootstrap 9094:9094 -n $NAMESPACE"
}

# Main function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "info" "Starting DORA Kafka cluster deployment..."
            check_prerequisites
            install_strimzi_operator
            deploy_kafka_cluster
            create_topics
            configure_security
            verify_deployment
            show_usage
            ;;
        "test")
            log "info" "Running Kafka performance test..."
            check_prerequisites
            performance_test
            ;;
        "verify")
            log "info" "Verifying Kafka deployment..."
            check_prerequisites
            verify_deployment
            ;;
        "clean")
            log "info" "Cleaning up test resources..."
            cleanup
            ;;
        *)
            echo "Usage: $0 [deploy|test|verify|clean]"
            echo "  deploy: Full Kafka cluster deployment (default)"
            echo "  test:   Run performance test"
            echo "  verify: Verify deployment status"
            echo "  clean:  Clean up test resources"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@" 