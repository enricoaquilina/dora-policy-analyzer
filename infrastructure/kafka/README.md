# DORA Compliance System - Apache Kafka Message Queue

This directory contains the Apache Kafka infrastructure configuration for the DORA Compliance System's asynchronous messaging and event streaming capabilities.

## Overview

Apache Kafka serves as the central message broker for:
- Inter-agent communication
- Event streaming between services
- Audit log streaming
- Real-time data processing
- Workflow orchestration events

## Architecture

### Kafka Cluster Setup
- **3 Kafka brokers** for high availability
- **3 Zookeeper nodes** for coordination (or KRaft mode for newer versions)
- **Confluent Schema Registry** for message schema management
- **Kafka Connect** for external system integration
- **Kafka Streams** for real-time processing

### Topic Design
```
dora-compliance/
├── agent-events          # Agent lifecycle and status events
├── task-requests         # Task assignment and execution requests
├── compliance-reports    # Generated compliance reports
├── audit-logs           # System audit events
├── incident-events      # ICT incident notifications
├── risk-assessments     # Risk calculation results
├── policy-updates       # Policy document changes
├── monitoring-metrics   # System performance metrics
└── dlq-*               # Dead letter queues for error handling
```

## Directory Structure

```
kafka/
├── README.md                    # This file
├── helm/                        # Helm charts and values
│   ├── kafka-cluster.yaml      # Main Kafka cluster configuration
│   ├── schema-registry.yaml    # Schema registry setup
│   ├── kafka-connect.yaml      # Kafka Connect configuration
│   └── monitoring.yaml         # Kafka monitoring stack
├── topics/                      # Topic configurations
│   ├── agent-topics.yaml       # Agent communication topics
│   ├── compliance-topics.yaml  # Compliance-related topics
│   ├── audit-topics.yaml       # Audit and logging topics
│   └── dlq-topics.yaml         # Dead letter queue topics
├── schemas/                     # Avro schemas for messages
│   ├── agent/                  # Agent-related schemas
│   ├── compliance/             # Compliance schemas
│   ├── audit/                  # Audit event schemas
│   └── common/                 # Shared schemas
├── security/                    # Security configurations
│   ├── ssl-config.yaml         # SSL/TLS configuration
│   ├── acl-config.yaml         # Access Control Lists
│   └── auth-config.yaml        # Authentication setup
├── monitoring/                  # Monitoring and alerting
│   ├── jmx-config.yaml         # JMX metrics configuration
│   ├── prometheus-rules.yaml   # Prometheus alerting rules
│   └── grafana-dashboards/     # Grafana dashboard definitions
└── scripts/                     # Utility scripts
    ├── setup-kafka.sh          # Kafka setup automation
    ├── topic-management.sh     # Topic management utilities
    └── performance-test.sh     # Performance testing scripts
```

## Prerequisites

- Kubernetes cluster (from subtask 1.2)
- Helm 3.0+
- kubectl configured
- Adequate storage (minimum 1TB per broker)
- Network bandwidth for replication

## Quick Start

### 1. Deploy Kafka Cluster
```bash
# Install Kafka operator
helm repo add strimzi https://strimzi.io/charts/
helm repo update

# Deploy Kafka cluster
kubectl apply -f helm/kafka-cluster.yaml
```

### 2. Configure Topics
```bash
# Create all topics
kubectl apply -f topics/
```

### 3. Set up Schema Registry
```bash
# Deploy Schema Registry
kubectl apply -f helm/schema-registry.yaml
```

### 4. Configure Security
```bash
# Apply security configurations
kubectl apply -f security/
```

## Topic Configuration

### Agent Communication Topics
- **agent-events**: Agent lifecycle, health, and status updates
- **task-requests**: Task assignment and execution requests
- **task-responses**: Task completion and result responses

### Compliance Topics
- **policy-analysis**: Policy document analysis results
- **gap-assessments**: Compliance gap identification
- **risk-calculations**: Risk scoring and assessment data
- **compliance-reports**: Generated compliance reports

### Audit Topics
- **audit-logs**: System audit trail
- **user-activities**: User action logging
- **data-access**: Data access audit logs

## Message Schemas

All messages use Avro schemas for:
- Type safety
- Schema evolution
- Backward/forward compatibility
- Data validation

### Schema Evolution Strategy
- **Backward Compatible**: New optional fields only
- **Forward Compatible**: Consumers can read newer schemas
- **Full Compatible**: Both backward and forward compatible

## Security Features

### Authentication & Authorization
- **SASL/SCRAM-SHA-256** for client authentication
- **ACLs** for fine-grained access control
- **mTLS** for broker-to-broker communication

### Encryption
- **TLS 1.3** for data in transit
- **Encryption at rest** for stored data
- **Schema encryption** for sensitive fields

## Performance Characteristics

### Throughput Targets
- **Writes**: 100,000 messages/second
- **Reads**: 500,000 messages/second
- **Latency**: < 10ms p95 for standard messages
- **Availability**: 99.99% uptime

### Partitioning Strategy
- **Agent topics**: Partitioned by agent ID
- **Compliance topics**: Partitioned by organization ID
- **Audit topics**: Partitioned by timestamp
- **Default partitions**: 12 per topic (3x broker count)

## Monitoring & Alerting

### Key Metrics
- Message throughput (messages/second)
- Consumer lag (messages behind)
- Broker resource utilization
- Replication lag between brokers
- Schema registry health

### Alerts
- Consumer lag > 10,000 messages
- Broker disk usage > 80%
- Replication lag > 5 seconds
- Schema registry unavailable
- Topic partition offline

## Disaster Recovery

### Backup Strategy
- **MirrorMaker 2.0** for cross-region replication
- **Topic snapshots** for point-in-time recovery
- **Schema registry backup** to S3
- **Configuration backup** in Git

### Recovery Procedures
1. Restore broker configuration
2. Recreate topics with same partitions
3. Restore schema registry
4. Resume replication
5. Validate data integrity

## Troubleshooting

Common issues and solutions:

### High Consumer Lag
```bash
# Check consumer group status
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group <group-id>

# Increase consumer instances
kubectl scale deployment <consumer-app> --replicas=10
```

### Broker Out of Disk Space
```bash
# Check disk usage
kubectl exec -it kafka-0 -- df -h

# Clean up old segments
kubectl exec -it kafka-0 -- kafka-log-dirs.sh --bootstrap-server localhost:9092 --describe
```

### Schema Evolution Issues
```bash
# Check schema compatibility
curl -X POST -H "Content-Type: application/json" \
  --data @new-schema.json \
  http://schema-registry:8081/compatibility/subjects/<subject>/versions/latest
```

## Development Guidelines

### Producer Best Practices
- Use idempotent producers
- Set appropriate `acks` and `retries`
- Implement proper error handling
- Use compression (gzip/snappy)

### Consumer Best Practices
- Process messages idempotently
- Commit offsets after processing
- Handle consumer rebalancing
- Monitor consumer lag

## Integration Patterns

### Event Sourcing
- Store events as immutable facts
- Replay events for state reconstruction
- Use compacted topics for snapshots

### CQRS (Command Query Responsibility Segregation)
- Separate write and read models
- Use Kafka for event propagation
- Materialize views from events

### Saga Pattern
- Coordinate distributed transactions
- Use compensation events for rollback
- Implement timeout handling

---

For detailed configuration and troubleshooting, see the individual configuration files and the [Kafka documentation](https://kafka.apache.org/documentation/).

Last Updated: December 2024 