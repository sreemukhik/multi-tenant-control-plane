# Multi Tenant Control Plane (Nexus)

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

---

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

---

## VPS / Production Setup Instructions (k3s)

### 1. Install k3s
```bash
curl -sfL https://get.k3s.io | sh -
# Configure access
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
export KUBECONFIG=~/.kube/config
```

### 2. Build and Push Images
```bash
# Export your registry
export REGISTRY=ghcr.io/your-username

# Build & Push
docker build -t $REGISTRY/multi-tenant-backend:latest backend/
docker build -t $REGISTRY/multi-tenant-dashboard:latest frontend/
docker push $REGISTRY/multi-tenant-backend:latest
docker push $REGISTRY/multi-tenant-dashboard:latest
```

### 3. Deploy via Helm
```bash
helm upgrade --install multi-tenant-platform ./helm/platform \
  --namespace multi-tenant-platform \
  --create-namespace \
  --values ./helm/platform/values-prod.yaml
```

---

## How to Create a Store and Place an Order

### 1. Create a Store
1.  Log in to the **Dashboard** -> **Stores** tab -> **"New Store"**.
2.  Enter a store name (e.g., `demo-store`) and select WooCommerce.
3.  The status will change to `Provisioning` as the operator creates the namespace, database, and WP instance.
4.  Wait for the status to become `Ready`.

### 2. Place an Order
1.  Click the **Store URL**.
2.  Add a product to your cart and proceed to **Checkout**.
3.  Select **Cash on Delivery** and place the order.
4.  Verify the order in the WordPress Admin panel (credentials in K8s Secrets).

---

##  Platform Engineering & Guardrails

To meet the requirements of a production-grade multi-tenant system, we implement several "platform-first" features:

### 1. Resource Isolation & Guardrails
- **Namespace Quotas:** Every tenant is constrained by a `ResourceQuota` (CPU: 1 Core, MEM: 1Gi) to prevent "noisy neighbor" issues.
- **LimitRanges:** Default CPU/Memory requests/limits are automatically injected into every pod.
- **Platform Integrity:** The `multi-tenant-platform` namespace has its own quota to ensure the API/Operator remains responsive.

### 2. Security Posture & RBAC
- **Principle of Least Privilege:** Simple `ServiceAccounts` are used for each component. The Operator uses a scoped `ClusterRole` specifically for managing `Store` CRDs and tenant namespaces.
- **Network Isolation:** Default-deny `NetworkPolicies` are applied, whitelist-only ingress from Traefik, and scoped egress for WP updates.
- **Secret Hygiene:** All passwords are generated on-the-fly, never stored in the application DB, and kept in `Kubernetes Secrets`.
- **Exposure Boundaries:** 
    - **Public:** Ingress (Dashboard, Store Frontends) via TLS-terminated endpoints.
    - **Internal:** API & Operator communicate via private `ClusterIP` services.
    - **Private:** Databases and internal caches are binded to local namespaces and strictly inaccessible from outside the cluster.

### 3. Horizontal Scaling & Upgrades
- **API/Dashboard:** Stateless components scale via `HorizontalPodAutoscaler` (HPA).
- **Operator Concurrency:** Supports **Leader Election** for HA. The reconciliation queue is bounded to prevent resource exhaustion during burst provisioning, with exponential backoff on retry.
- **Upgrades & Rollbacks:** 
    - Full support for `helm upgrade` and `helm rollback`.
    - Version pinning for all engine components (WordPress, MySQL).
    - Rolling update strategies ensure zero-downtime for management plane components.

### 4. Abuse Prevention & Governance
- **Rate Limiting:** API-level sliding-window limits per user.
- **Tenant Quotas:** Strict `MAX_STORES_PER_USER` enforcement.
- **Provisioning Timeouts:** Automated failure marking if a store takes >10 minutes to provision.
- **Audit Logs:** Every lifecycle event (provision, delete, scale) is logged with metadata and IP tracking.

---

##  System Design & Tradeoffs

### Architecture Choice: Controller-Operator Pattern
*   **Control Plane (FastAPI):** Handles lightweight API requests and persists "intent" (CRDs).
*   **Operator (Kopf):** Runs asynchronously to handle heavy lifting (Helm, DBs) via idempotent loops.
*   **Tradeoff:** Separates user-facing latency from infrastructure latency. API responses are instant, while complex K8s operations happen in the background with robust retries.

### Idempotency & Failure Handling
*   **Idempotency:** The operator logic is re-runnable. If a step fails, it retries without duplicating resources.
*   **Cleanup:** We use **Kubernetes Finalizers**. Deleting a store triggers a graceful cleanup of the namespace, PVC, and database before the object is removed.

###  Failure Scenarios & Recovery
Nexus is built to tolerate infrastructure instability:
- **Helm Install Fails:** Status is marked as `Failed` with the exact error reason surfaced to the UI for user intervention.
- **Partial Namespace Creation:** Reconciliation resumes automatically, completing only the missing resources.
- **Operator Restart:** Reconstruction of state happens automatically as Kopf resumes watching the CRD desired state.
- **PVC Deletion Hangs:** Kubernetes finalizers block the `Store` deletion until cleanup succeeds, preventing orphaned data.

---

## � Production Considerations (Local vs. Prod)
- **DNS:** Wildcard DNS (`*.example.com`) replaces `*.localhost`.
- **TLS:** Production uses `Cert-Manager` with Let's Encrypt for automatic HTTPS.
- **Storage:** Upgrade from `local-path` to cloud-native CSI drivers (e.g., `gp3`, `longhorn`).
- **Secrets:** Leverage External Secrets or Sealed Secrets for management plane credentials.

