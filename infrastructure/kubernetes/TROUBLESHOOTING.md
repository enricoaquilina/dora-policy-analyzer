# Kubernetes Infrastructure Troubleshooting Guide

## Table of Contents
1. [Common Issues](#common-issues)
2. [Cluster Access Issues](#cluster-access-issues)
3. [Node Issues](#node-issues)
4. [Pod Issues](#pod-issues)
5. [Storage Issues](#storage-issues)
6. [Networking Issues](#networking-issues)
7. [Performance Issues](#performance-issues)
8. [Security Issues](#security-issues)
9. [Useful Commands](#useful-commands)
10. [Emergency Procedures](#emergency-procedures)

## Common Issues

### Issue: Cluster deployment fails
**Symptoms:** Terraform apply fails during cluster creation

**Resolution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify terraform state
terraform state list

# Check for resource limits
aws service-quotas list-service-quotas --service-code eks

# Clean up and retry
terraform destroy -target=module.eks
terraform apply
```

### Issue: kubectl commands timeout
**Symptoms:** `Unable to connect to the server: dial tcp: i/o timeout`

**Resolution:**
```bash
# Update kubeconfig
aws eks update-kubeconfig --name dora-compliance-prod --region eu-west-1

# Check cluster status
aws eks describe-cluster --name dora-compliance-prod

# Verify security groups allow access
aws ec2 describe-security-groups --group-ids <cluster-security-group-id>
```

## Cluster Access Issues

### Issue: Authentication errors
**Symptoms:** `error: You must be logged in to the server (Unauthorized)`

**Resolution:**
```bash
# Verify AWS IAM role/user
aws sts get-caller-identity

# Check aws-auth ConfigMap
kubectl -n kube-system get configmap aws-auth -o yaml

# Add user/role to aws-auth if missing
kubectl -n kube-system edit configmap aws-auth
```

### Issue: RBAC permission denied
**Symptoms:** `Error from server (Forbidden): pods is forbidden`

**Resolution:**
```bash
# Check current user's permissions
kubectl auth can-i --list

# Verify ClusterRoleBindings
kubectl get clusterrolebindings | grep dora

# Check specific role
kubectl describe clusterrole dora-operator
```

## Node Issues

### Issue: Nodes not ready
**Symptoms:** Nodes show `NotReady` status

**Resolution:**
```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check kubelet logs
kubectl logs -n kube-system <kubelet-pod>

# SSH to node (if needed)
aws ssm start-session --target <instance-id>

# On the node, check kubelet
sudo systemctl status kubelet
sudo journalctl -u kubelet -f
```

### Issue: Node capacity issues
**Symptoms:** Pods stuck in `Pending` due to insufficient resources

**Resolution:**
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check cluster autoscaler logs
kubectl -n kube-system logs -l app=cluster-autoscaler

# Manually scale node group if needed
aws eks update-nodegroup-config \
  --cluster-name dora-compliance-prod \
  --nodegroup-name agent-node-group \
  --scaling-config minSize=5,maxSize=50,desiredSize=15
```

## Pod Issues

### Issue: Pods crash looping
**Symptoms:** Pod status shows `CrashLoopBackOff`

**Resolution:**
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Describe pod for events
kubectl describe pod <pod-name> -n <namespace>

# Check resource limits
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 resources:

# Debug with ephemeral container
kubectl debug <pod-name> -n <namespace> -it --image=busybox
```

### Issue: Image pull errors
**Symptoms:** `ErrImagePull` or `ImagePullBackOff`

**Resolution:**
```bash
# Check image name and tag
kubectl describe pod <pod-name> -n <namespace> | grep Image:

# Verify registry credentials
kubectl get secrets -n <namespace>

# Check node's ability to pull
kubectl run test-pull --image=<image-name> --restart=Never
```

## Storage Issues

### Issue: PVC stuck in Pending
**Symptoms:** PersistentVolumeClaim remains in `Pending` status

**Resolution:**
```bash
# Check PVC events
kubectl describe pvc <pvc-name> -n <namespace>

# Verify storage class exists
kubectl get storageclass

# Check if PV exists for static provisioning
kubectl get pv

# Check EBS CSI driver
kubectl -n kube-system get pods -l app=ebs-csi-controller

# Verify IAM permissions for EBS CSI
kubectl -n kube-system describe sa ebs-csi-controller-sa
```

### Issue: Volume mount failures
**Symptoms:** `Unable to attach or mount volumes`

**Resolution:**
```bash
# Check volume attachment on node
kubectl get volumeattachments

# Verify EBS volume state
aws ec2 describe-volumes --volume-ids <volume-id>

# Check CSI driver logs
kubectl -n kube-system logs -l app=ebs-csi-controller
```

## Networking Issues

### Issue: Service not accessible
**Symptoms:** Cannot reach service endpoints

**Resolution:**
```bash
# Check service endpoints
kubectl get endpoints <service-name> -n <namespace>

# Verify pod labels match service selector
kubectl get pods -n <namespace> --show-labels

# Test connectivity from within cluster
kubectl run test-net --image=busybox --rm -it -- wget -qO- <service-name>.<namespace>:port

# Check network policies
kubectl get networkpolicies -n <namespace>
```

### Issue: DNS resolution failures
**Symptoms:** `nslookup: can't resolve 'service-name'`

**Resolution:**
```bash
# Check CoreDNS pods
kubectl -n kube-system get pods -l k8s-app=kube-dns

# Test DNS from a pod
kubectl run test-dns --image=busybox --rm -it -- nslookup kubernetes.default

# Check CoreDNS logs
kubectl -n kube-system logs -l k8s-app=kube-dns

# Restart CoreDNS if needed
kubectl -n kube-system rollout restart deployment coredns
```

## Performance Issues

### Issue: Slow API responses
**Symptoms:** kubectl commands take long time

**Resolution:**
```bash
# Check API server metrics
kubectl top nodes
kubectl -n kube-system top pods

# Check etcd performance
kubectl -n kube-system exec etcd-<node> -- etcdctl endpoint status

# Review API server logs
kubectl -n kube-system logs kube-apiserver-<node>

# Scale up control plane if needed
```

### Issue: High memory/CPU usage
**Symptoms:** Nodes showing high resource utilization

**Resolution:**
```bash
# Find resource-hungry pods
kubectl top pods --all-namespaces | sort -k3 -nr | head -20

# Check for memory leaks
kubectl describe nodes | grep -A 5 "Non-terminated Pods"

# Set resource limits
kubectl set resources deployment <name> -n <namespace> --limits=memory=2Gi,cpu=1
```

## Security Issues

### Issue: Pod security policy violations
**Symptoms:** Pods fail to start with PSP errors

**Resolution:**
```bash
# Check PSP
kubectl get psp
kubectl describe psp dora-restricted

# Verify service account has PSP access
kubectl get rolebindings,clusterrolebindings --all-namespaces -o wide | grep psp

# Check pod security context
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 securityContext:
```

### Issue: Secret access denied
**Symptoms:** `secrets "secret-name" is forbidden`

**Resolution:**
```bash
# Check service account
kubectl get pod <pod-name> -n <namespace> -o yaml | grep serviceAccount

# Verify RBAC rules
kubectl get rolebindings -n <namespace>
kubectl describe rolebinding <binding-name> -n <namespace>

# Grant access if needed
kubectl create rolebinding secret-reader \
  --role=secret-reader \
  --serviceaccount=<namespace>:<service-account> \
  -n <namespace>
```

## Useful Commands

### Cluster Information
```bash
# Cluster info
kubectl cluster-info
kubectl get componentstatuses

# Node information
kubectl get nodes -o wide
kubectl describe nodes

# Resource usage
kubectl top nodes
kubectl top pods --all-namespaces
```

### Debugging Commands
```bash
# Get all resources in a namespace
kubectl get all -n <namespace>

# Get events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Resource YAML
kubectl get <resource> <name> -n <namespace> -o yaml

# API resources
kubectl api-resources

# Explain resource fields
kubectl explain pod.spec.containers
```

### Cleanup Commands
```bash
# Delete evicted pods
kubectl get pods --all-namespaces | grep Evicted | awk '{print $2 " --namespace=" $1}' | xargs kubectl delete pod

# Delete completed jobs
kubectl delete jobs --field-selector status.successful=1

# Clean up failed pods
kubectl delete pods --field-selector status.phase=Failed --all-namespaces
```

## Emergency Procedures

### Cluster Recovery
1. **Check cluster health:**
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces | grep -v Running
   ```

2. **Backup critical data:**
   ```bash
   kubectl get all --all-namespaces -o yaml > cluster-backup.yaml
   ```

3. **Restart critical components:**
   ```bash
   # Restart CoreDNS
   kubectl -n kube-system rollout restart deployment coredns
   
   # Restart kube-proxy
   kubectl -n kube-system rollout restart daemonset kube-proxy
   ```

### Node Recovery
1. **Cordon node:**
   ```bash
   kubectl cordon <node-name>
   ```

2. **Drain workloads:**
   ```bash
   kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
   ```

3. **Fix node issues**

4. **Uncordon node:**
   ```bash
   kubectl uncordon <node-name>
   ```

### Rollback Procedures
1. **Deployment rollback:**
   ```bash
   kubectl rollout history deployment <name> -n <namespace>
   kubectl rollout undo deployment <name> -n <namespace>
   ```

2. **Helm rollback:**
   ```bash
   helm list -n <namespace>
   helm rollback <release> <revision> -n <namespace>
   ```

---

For additional support, consult the [Kubernetes documentation](https://kubernetes.io/docs/) or contact the platform team. 