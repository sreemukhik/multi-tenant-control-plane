# Architecture & Design

## Overview
Urumi is an **enterprise-grade provisioning platform** for multi-tenant WooCommerce hosting on Kubernetes. It separates concerns into a Control Plane (API/Orchestrator) and a Data Plane (Kubernetes Workloads).

## Core Components

### 1. Control Plane (Backend)
- **FastAPI Service**: Handles REST API requests, validation, and policy enforcement.
- **Orchestrator**: Async background worker that manages the lifecycle of Helm releases.
- **PostgreSQL**: Stores tenant configuration, provisioning status, and audit logs.

### 2. Execution Plane (Kubernetes)
- **Helm**: The provisioning engine. We use the **Bitnami WordPress Chart** for production readiness.
- **Namespaces**: Strict isolation boundary per tenant.
- **Ingress Controller**: Traefik/Nginx routing traffic to individual store services.

## Key Design Decisions

1.  **Explicit Orchestration vs. Operator**: 
    -   We chose a backend-driven approach over a custom Kubernetes Operator. This simplifies debugging (standard Python code) and allows easier integration with external billing/auth systems.

2.  **Namespace-per-Tenant**:
    -   Provides the strongest isolation for security (RBAC) and resource management (Quotas).
    -   Prevents "noisy neighbor" issues via ResourceQuotas.

3.  **Bitnami Charts**:
    -   Instead of maintaining custom charts, we leverage Bitnami's industry-standard charts for security updates and best practices.

## Security Model

-   **RBAC**: ServiceAccount has least-privilege access, scoped only to necessary namespaces.
-   **Secrets**: All passwords (DB, Admin) are auto-generated and stored as K8s Secrets.
-   **Network Policies**: (Planned) Default deny-all, allowing only Ingress->App->DB traffic.

## Scalability

-   **Horizontal Scaling**: The API and Dashboard are stateless and can auto-scale based on CPU load.
-   **Database**: Each tenant gets a dedicated MariaDB instance (via chart), ensuring data isolation and independent scaling/backup.

For a detailed walkthrough of the system flow and demo script, see [DEMO.md](./DEMO.md).
