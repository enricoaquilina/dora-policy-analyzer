# Cluster Autoscaler IAM Role
module "cluster_autoscaler_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.30"
  
  role_name = "${var.cluster_name}-cluster-autoscaler"
  
  attach_cluster_autoscaler_policy = true
  cluster_autoscaler_cluster_ids   = [module.eks.cluster_name]
  
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:cluster-autoscaler"]
    }
  }
}

# Helm provider configuration
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Install Cluster Autoscaler using Helm
resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = "9.34.0"
  namespace  = "kube-system"
  
  set {
    name  = "autoDiscovery.clusterName"
    value = module.eks.cluster_name
  }
  
  set {
    name  = "awsRegion"
    value = var.region
  }
  
  set {
    name  = "rbac.serviceAccount.create"
    value = "true"
  }
  
  set {
    name  = "rbac.serviceAccount.name"
    value = "cluster-autoscaler"
  }
  
  set {
    name  = "rbac.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = module.cluster_autoscaler_irsa.iam_role_arn
  }
  
  set {
    name  = "extraArgs.balance-similar-node-groups"
    value = "true"
  }
  
  set {
    name  = "extraArgs.skip-nodes-with-system-pods"
    value = "false"
  }
  
  set {
    name  = "extraArgs.scale-down-utilization-threshold"
    value = "0.7"
  }
  
  set {
    name  = "resources.requests.cpu"
    value = "100m"
  }
  
  set {
    name  = "resources.requests.memory"
    value = "300Mi"
  }
  
  set {
    name  = "resources.limits.cpu"
    value = "200m"
  }
  
  set {
    name  = "resources.limits.memory"
    value = "500Mi"
  }
  
  set {
    name  = "nodeSelector.role"
    value = "system"
  }
  
  depends_on = [module.eks, module.cluster_autoscaler_irsa]
}

# Metrics Server for HPA
resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  version    = "3.11.0"
  namespace  = "kube-system"
  
  set {
    name  = "args[0]"
    value = "--kubelet-insecure-tls"
  }
  
  set {
    name  = "nodeSelector.role"
    value = "system"
  }
  
  depends_on = [module.eks]
} 