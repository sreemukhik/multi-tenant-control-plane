# Production Deployment Guide

This guide outlines the steps and considerations for deploying the Urumi Store Platform in a production-ready environment using k3s on a VPS.

## Infrastructure Prerequisites

*   Hardware: 2 vCPU, 4GB RAM minimum (per node).
*   OS: Ubuntu 22.04 LTS (recommended).
*   Network: A public IP and a domain name with control over DNS (specifically wildcard subdomains).

## 1. Kubernetes Distribution: k3s

k3s is chosen for its lightweight footprint and ease of management on a single VPS.

### Installation

```bash
curl -sfL https://get.k3s.io | sh -
```

### Access Configuration

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
```

## 2. Ingress and DNS Strategy

In production, we use a wildcard DNS record to handle multi-tenancy.

*   Wildcard Record: `*.yourdomain.com` -> `VPS_PUBLIC_IP`
*   Platform Dashboard: `dashboard.yourdomain.com`
*   Platform API: `api.yourdomain.com`

The bundled Traefik ingress controller in k3s will route traffic based on Host headers to the appropriate store namespace.

## 3. Security Hardening

### Network Policies

For production, namespaces should be isolated using NetworkPolicies. The Urumi platform applies a default deny policy that only allows:
*   Ingress traffic from the Traefik LB.
*   Egress traffic to necessary services (DNS, API).
*   Internal namespace traffic (App to MariaDB).

### Resource Quotas

To prevent a single tenant from exhausting VPS resources, every store namespace is automatically provisioned with a `ResourceQuota` limiting CPU (1 Core) and Memory (1Gi).

## 4. TLS with Cert-Manager

Automating SSL certificates is critical for security.

### Installation

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

### ClusterIssuer Configuration

We recommend using Let's Encrypt for free, automated certificates.

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
```

## 5. Storage Classes

k3s defaults to `local-path` storage. For multi-node or high-availability production, consider:
*   Longhorn: Distributed block storage for Kubernetes.
*   Cloud-specific: `ebs-sc` (AWS) or `pd-standard` (GCP).

Update the `storageClass` field in `values-prod.yaml` accordingly.

## 6. Secrets Management

Passwords and sensitive tokens should never be stored in plaintext.
*   The Operator automatically generates secure passwords for every store and saves them as Kubernetes Secrets.
*   For platform-level secrets (DB passwords), use a `values-prod.yaml` override or a tool like Sealed Secrets / External Secrets operator.

## 7. Scaling and Availability

The platform components are stateless and can be scaled horizontally:

```bash
kubectl scale deployment urumi-platform-api --replicas=3 -n urumi-platform
kubectl scale deployment urumi-dashboard --replicas=3 -n urumi-platform
```
