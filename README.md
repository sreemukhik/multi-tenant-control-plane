#  Multi-tenant Store Platform

Urumi is an enterprise-grade provisioning platform for multi-tenant WooCommerce hosting on Kubernetes. It provides a full-stack solution for managing store lifecycles, from automated deployment to health monitoring and audit logging.

## Directory Structure

*   backend/: FastAPI control plane and Kubernetes Operator (Kopf).
*   frontend/: React-based administrative dashboard.
*   helm/: Deployment charts for the platform and store engines.
*   scripts/: Automation scripts for local and production environment setup.

## Technical Stack

*   Backend: Python, FastAPI, SQLAlchemy, Kopf (Kubernetes Operator Framework).
*   Frontend: React, TypeScript, Vite, Tailwind CSS, TanStack Query.
*   Infrastructure: Kubernetes (k3d/k3s), Helm, PostgreSQL, MariaDB (for stores).
*   Store Engine: WordPress with WooCommerce (via Bitnami Helm charts).

## Local Setup Instructions

### Prerequisites

*   Docker Desktop or Docker Engine
*   k3d (Kubernetes in Docker)
*   Helm v3+
*   kubectl

### 1. Initialize the Cluster

Run the provided setup script to create a k3d cluster and build/import the necessary component images:

```bash
chmod +x scripts/setup-local.sh
./scripts/setup-local.sh
```

For Windows users (PowerShell):
```powershell
./scripts/setup-local.ps1
```

### 2. Platform Access

After running the setup script, the platform will be available via the Ingress controller. Access details are dynamically managed and provided in the script output.

## Core Features

*   **Automated Multi-Tenant Provisioning**: Isolated namespaces for every store with dedicated MariaDB instances.
*   **Live Observability Dashboard**: Real-time tracking of resource usage, provisioning status, and precision build timers.
*   **Comprehensive Audit Logging**: Every administrative action and provisioning step is logged for transparency and debugging.
*   **Enterprise-Grade Hardening**: Automatic application of Kubernetes ResourceQuotas and NetworkPolicies for tenant isolation.
*   **Idempotent Workflows**: Robust provisioning logic designed to handle interruptions and retries gracefully.

## VPS / Production Setup Instructions (k3s)

The production setup assumes a clean Linux VPS (e.g., Ubuntu 22.04).

### 1. Install k3s

```bash
curl -sfL https://get.k3s.io | sh -
# Ensure k3s is accessible
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
```

### 2. Build and Push Images

Build the platform images and push them to your container registry (e.g., GitHub Packages or Docker Hub):

```bash
docker build -t your-reg/urumi-platform-api:v1 backend/
docker build -t your-reg/urumi-dashboard:v1 frontend/
docker push your-reg/urumi-platform-api:v1
docker push your-reg/urumi-dashboard:v1
```

### 3. Deploy via Helm

Update helm/platform/values-prod.yaml with your domain names, database credentials, and container registry paths.

```bash
helm upgrade --install urumi-platform ./helm/platform \
    --namespace urumi-platform \
    --create-namespace \
    --values ./helm/platform/values-prod.yaml
```

### 4. Configure External DNS

Point your base domain and the following subdomains to your VPS public IP:

*   dashboard.yourdomain.com
*   api.yourdomain.com
*   *.yourdomain.com (Wildcard for store namespaces)

## Usage Guide

### Creating a Store

1.  Navigate to the Stores section in the Dashboard.
2.  Click "New Store".
3.  Enter a unique name and select the engine (currently WooCommerce).
4.  The platform will immediately mark the status as "Provisioning".
5.  Internal logic will create a dedicated Kubernetes namespace, apply resource quotas, install the Helm release, and seed initial products.

### Placing an Order

1.  Once the store status is "Ready", click "Details".
2.  Open the Storefront URL provided in the metadata section.
3.  Browse the seeded products (e.g., Premium Cotton T-Shirt).
4.  Add a product to the cart and proceed to checkout.
5.  The platform activates "Cash on Delivery" by default for all new stores to facilitate immediate testing.
6.  Complete the checkout process to place a test order.

## System Design and Tradeoffs

### Architecture Choice

The platform utilizes a hybrid Control Plane + Kubernetes Operator approach:

*   FastAPI Control Plane: Manages the REST interface and state persistence in PostgreSQL.
*   Custom Resource Definitions (CRD): When a store is requested, the API creates a 'Store' custom resource in Kubernetes.
*   Kopf-based Operator: Monitors 'Store' resources and executes the heavy-lifting (Helm logic, WooCommerce CLI configuration, hardening) asynchronously.

This separation ensures the API remains responsive while complex provisioning logic runs reliably in the background with automatic retries.

### Idempotency and Failure Handling

*   Helm Integration: Provisioning is performed via `helm upgrade --install`, ensuring that re-running the logic for the same store name is safe.
*   Seeding Logic: The operator checks for existing products via the WooCommerce CLI before attempting creation to prevent duplicates.
*   Timed Retries: If a provisioning step fails (e.g., network timeout), Kopf handles the retry logic based on defined backoff strategies.
*   Cleanup: Deleting a store triggers a finalizer in the operator that uninstalls the Helm release and removes the associated namespace, ensuring no orphaned resources remain.

### Production Readiness Adjustments

To transition from local k3d to a production environment, the following changes are implemented in values-prod.yaml:

*   DNS: Uses real domain names instead of .local suffixes.
*   Ingress: Enables TLS termination via Cert-Manager (Let's Encrypt).
*   Storage: Configures a persistent StorageClass (e.g., Longhorn or EBS) instead of hostPath.
*   Secrets: Management of database and admin passwords should be handled via Kubernetes Secrets or an external Vault.
*   Hardening: Production namespaces apply strict NetworkPolicies to isolate tenant workloads from the management plane.
