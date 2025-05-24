# DORA Compliance System - Kubernetes Infrastructure

This directory contains all the configuration and setup files for the DORA Compliance System Kubernetes infrastructure.

## Directory Structure

```
kubernetes/
├── README.md                    # This file
├── clusters/                    # Cluster-specific configurations
│   ├── development/            # Development cluster configs
│   ├── staging/                # Staging cluster configs
│   └── production/             # Production cluster configs
├── namespaces/                 # Namespace definitions
├── rbac/                       # RBAC policies and roles
├── storage/                    # Storage classes and PV configs
├── networking/                 # Network policies and ingress
├── monitoring/                 # Monitoring stack configs
├── security/                   # Security policies and PSPs
├── helm/                       # Helm charts
│   ├── charts/                # Custom helm charts
│   └── values/                # Environment-specific values
└── scripts/                    # Utility scripts
```

## Prerequisites

- Kubernetes 1.28+
- kubectl CLI tool
- Helm 3.0+
- Terraform 1.6+ (for cloud provider setup)
- Cloud provider CLI (AWS CLI, gcloud, az)

## Quick Start

### 1. Install Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installations
kubectl version --client
helm version
```

### 2. Choose Your Environment

- **Development**: Single-node or minimal cluster for development
- **Staging**: Multi-node cluster mimicking production
- **Production**: Full HA cluster with all features enabled

### 3. Apply Base Configuration

```bash
# Set your environment
export ENVIRONMENT=development  # or staging, production

# Apply namespace configuration
kubectl apply -f namespaces/

# Apply RBAC configuration
kubectl apply -f rbac/

# Apply storage configuration
kubectl apply -f storage/

# Apply network policies
kubectl apply -f networking/
```

## Cluster Architecture

### Master Nodes (Control Plane)
- 3 master nodes for HA (production)
- etcd cluster for state management
- API server with load balancing
- Controller manager and scheduler

### Worker Node Pools
1. **Agent Pool**: For running AI/ML agents
   - High CPU/memory nodes
   - GPU support for ML workloads
   - Auto-scaling enabled

2. **Data Pool**: For databases and storage
   - High IOPS storage
   - Local SSD for performance
   - Fixed size for stability

3. **Gateway Pool**: For ingress and API gateway
   - Network optimized
   - Public-facing
   - Auto-scaling enabled

## Namespaces

- `dora-system`: Core system components
- `dora-agents`: AI/ML agents
- `dora-data`: Databases and storage
- `dora-monitoring`: Monitoring and logging
- `dora-security`: Security tools and scanners

## High Availability Configuration

Production cluster uses:
- Multi-master setup across 3 availability zones
- Pod disruption budgets for critical services
- Node affinity rules for workload distribution
- Automatic failover and self-healing

## Security Features

- Network policies for pod-to-pod communication
- Pod Security Policies (PSPs) enforced
- RBAC with principle of least privilege
- Secrets encryption at rest
- Audit logging enabled
- mTLS between services via Istio

## Monitoring & Observability

- Prometheus for metrics collection
- Grafana for visualization
- ELK stack for log aggregation
- Jaeger for distributed tracing
- Custom dashboards for DORA compliance

## Backup & Disaster Recovery

- etcd snapshots every 6 hours
- Persistent volume snapshots
- Cross-region cluster replication
- Automated restore procedures
- Regular DR drills

## Maintenance

- Rolling updates for zero downtime
- Automated certificate rotation
- Node auto-repair enabled
- Cluster autoscaler configured
- Regular security patches

## Troubleshooting

Common issues and solutions are documented in [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Support

For issues or questions:
- Check the troubleshooting guide
- Review cluster logs
- Contact the platform team

---
Last Updated: December 2024 