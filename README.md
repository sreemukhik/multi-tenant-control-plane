# Multi Tenant Control Plane

Multi Tenant Control Plane is an enterprise-grade provisioning platform for multi-tenant WooCommerce hosting on Kubernetes. It provides a full-stack solution for managing store lifecycles, from automated deployment to health monitoring and audit logging.

## Directory Structure & Source Code

*   **Dashboard (Frontend):** `frontend/`
    *   React-based administrative dashboard using Vite, Tailwind CSS, and TanStack Query.
*   **Control Plane (Backend):** `backend/app/`
    *   **API:** FastAPI service for handling user requests and maintaining state.
    *   **Orchestration:** `backend/app/operator/` contains the Kopf-based operator logic that manages Kubernetes resources.
*   **Helm Charts:** `helm/`
    *   `helm/platform/`: Chart for deploying the Multi Tenant Control Plane (API + Dashboard).
    *   `helm/store-engines/`: Charts used to provision individual stores (e.g., WooCommerce).
*   **Scripts:** `scripts/`
    *   Automation scripts for local development (`setup-local.sh`, `setup-local.ps1`) and other utilities.

## Local Setup Instructions

### Prerequisites
*   Docker Desktop or Docker Engine
*   k3d (Kubernetes in Docker) or similar local K8s cluster
*   Helm v3+
*   kubectl
*   Python 3.10+ (for local backend development)

### Quick Start (Automated)

We provide automated scripts to spin up a local development environment using k3d.

**For Linux/Mac:**
```bash
chmod +x scripts/setup-local.sh
./scripts/setup-local.sh
```

**For Windows (PowerShell):**
```powershell
./scripts/setup-local.ps1
```

This script will:
1.  Create a k3d cluster named `multi-tenant-cluster`.
2.  Build the backend and frontend Docker images.
3.  Import images into the cluster.
4.  Install the `helm/platform` chart.
5.  Wait for all pods to be ready.

## VPS / Production Setup Instructions (k3s)

This guide assumes a clean Linux VPS (Ubuntu 22.04 recommended) with a public IP and a domain name.

### 1. Install k3s
Install a lightweight Kubernetes distribution:
```bash
curl -sfL https://get.k3s.io | sh -
# Configure access
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
export KUBECONFIG=~/.kube/config
```

### 2. Build and Push Images
You need to build the images locally and push them to a container registry (e.g., Docker Hub, GitHub Container Registry).

```bash
# Export your registry
export REGISTRY=ghcr.io/your-username

# Build
docker build -t $REGISTRY/multi-tenant-backend:latest backend/
docker build -t $REGISTRY/multi-tenant-dashboard:latest frontend/

# Push
docker push $REGISTRY/multi-tenant-backend:latest
docker push $REGISTRY/multi-tenant-dashboard:latest
```

### 3. Configure Helm for Production
Edit `helm/platform/values-prod.yaml` to match your environment:
*   **Domain:** Update `global.domain` to your actual domain (e.g., `example.com`).
*   **Images:** Update `image.repository` to match your registry URLs.
*   **Storage:** Change `storageClass` if you are using a specific provider (e.g., `longhorn`, `gp2`).
*   **Secrets:** Update database passwords.

### 4. Deploy via Helm
```bash
helm upgrade --install multi-tenant-platform ./helm/platform \
  --namespace multi-tenant-platform \
  --create-namespace \
  --values ./helm/platform/values-prod.yaml
```

### 5. DNS Configuration
Point the following DNS records to your VPS IP:
*   `api.example.com` (A Record)
*   `dashboard.example.com` (A Record)
*   `*.example.com` (Wildcard A Record for customer stores)

## How to Create a Store and Place an Order

### 1. Create a Store
1.  Log in to the **Dashboard**.
2.  Navigate to the **Stores** tab.
3.  Click **"New Store"**.
4.  Enter a unique store name (e.g., `demo-store`) and select the plan/engine (WooCommerce).
5.  Click **Create**.
6.  The status will change to `Provisioning`. The operator is now creating a namespace, database, and installing WordPress in the background.
7.  Wait for the status to become `Ready`.

### 2. Place an Order
1.  Once `Ready`, click the **Store URL** (e.g., `http://demo-store.example.com` or `.localhost`).
2.  Browse the storefront. The provisioning process automatically seeds example products.
3.  Add a product (e.g., "Premium T-Shirt") to your cart.
4.  Proceed to **Checkout**.
5.  Enter sample billing details.
6.  Select **Cash on Delivery** (enabled by default for testing).
7.  Place the order.
8.  You can verify the order in the WordPress Admin panel (credentials are stored in Kubernetes Secrets).

## System Design & Tradeoffs

### Architecture Choice
We utilize a **Controller-Operator Pattern**:
*   **Control Plane (FastAPI):** Handles lightweight tasks: API requests, authentication, and persisting intent (Store CRDs) to the database/Kubernetes.
*   **Operator (Kopf):** Runs asynchronously to handle heavy lifting. It watches for `Store` CRD changes and executes idempotent provisioning loops (Helm installs, DB creation, file operations).
*   **Tradeoff:** This separates user-facing latency from infrastructure latency. API responses are instant ("Provisioning started"), while the complex K8s operations happen in the background with robust retry mechanisms.

### Idempotency & Failure Handling
*   **Idempotency:** The operator logic is designed to be re-runnable. If a step fails (e.g., Helm upgrade), the operator retries from the current state without duplicating resources.
*   **Failure Handling:** We use Kopf's built-in retry backoff. Temporary network blips will just cause a delayed success. Permanent failures are logged to the `Store` status for the user to see.
*   **Cleanup:** We use Kubernetes **Finalizers**. When a `Store` is deleted, the operator intercepts the deletion, uninstalls the Helm chart, deletes the namespace and database volume, and only then allows the `Store` object to be removed. This prevents orphaned resources.

### Production Considerations (Local vs. Prod)
Transitioning to production requires addressing several layers:
*   **DNS:** Moved from `*.localhost` to real wildcard DNS (`*.example.com`).
*   **Ingress:** Traefik/Nginx must be configured with a valid `ClusterIssuer` (Cert-Manager) for automatic Let's Encrypt SSL/TLS, unlike the self-signed/HTTP approach locally.
*   **Storage Class:** Local setups use `local-path` or `standard`. Production should use specific CSI drivers (e.g., `gp3` on AWS, `longhorn` for VPS chunks) for persistence and backups.
*   **Secrets:** In local, we might default to simple secrets. In production, `values-prod.yaml` should leverage External Secrets or sealed secrets, and all default passwords must be rotated.
