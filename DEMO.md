# 🎥 Urumi Store Platform - Demo Script & Guide

This guide covers all key aspects of the platform for your demo video, aligned with the project requirements.

---

## 1. System Design & Implementation

**Core Concept:**
"Urumi is a multi-tenant platform that automates the provisioning of WooCommerce stores on Kubernetes. It uses a **Control Plane / Data Plane** architecture where a Python FastAPI backend orchestrates Helm charts to deploy isolated store environments."

**Components:**
1.  **Frontend (Dashboard):**
    -   React + TypeScript application for store management.
    -   Provides real-time provisioning status updates via polling.
    -   Visualizes system metrics and audit logs.
2.  **Backend (Control Plane):**
    -   **FastAPI Service:** Handles API requests, authentication, and validation.
    -   **Orchestrator:** Asynchronous background worker that manages Helm releases.
    -   **PostgreSQL Database:** Stores tenant metadata, provisioning status, and audit logs.
3.  **Infrastructure (Data Plane):**
    -   **Kubernetes Cluster:** Hoster for all tenant workloads.
    -   **Helm:** The provisioning engine. We use the production-grade **Bitnami WordPress Chart** for stability and security.
    -   **Ingress Controller:** Routes traffic to specific stores based on subdomains (e.g., `store-abc.k8s.local`).

**End-to-End Flow (Demo Walkthrough):**
1.  **User Request:** User clicks "Create Store" on the Dashboard.
2.  **API Validation:** Backend validates the request and creating a `requested` record in DB.
3.  **Async Provisioning:**
    -   A background task picks up the request.
    -   It triggers `helm install` with a unique namespace (e.g., `store-xyz`).
    -   It injects secure, auto-generated passwords for MariaDB and WordPress.
4.  **Resource Creation:** Kubernetes creates:
    -   `Namespace` (Isolation boundary)
    -   `StatefulSet` (MariaDB storage)
    -   `Deployment` (WordPress application)
    -   `Service` & `Ingress` (Networking)
    -   `Secret` (Credentials)
5.  **Completion:** The store becomes `Ready`. The URL is returned to the dashboard.
6.  **Deletion:** Clicking "Delete" triggers `helm uninstall` and namespace cleanup, removing all associated resources.

---

## 2. Isolation, Resources, & Reliability

**Isolation Strategy:**
-   **Namespace-per-Tenant:** Every store lives in its own Kubernetes Namespace. This provides the strongest isolation boundary, ensuring network policies and RBAC can be scoped strictly to one tenant.
-   **Storage Isolation:** Each store gets its own `PersistentVolumeClaim` (PVC) for the database and WordPress files (via Bitnami chart configuration), ensuring data never leaks between tenants.

**Resource Management:**
-   **Requests & Limits:** The Helm chart is configured with CPU/Memory requests (guaranteed) and limits (burst capacity) to prevent "noisy neighbor" problems.
-   **Resource Quotas:** We apply `ResourceQuota` objects to each namespace to cap total consumption (e.g., max 2GB RAM per store), preventing any single tenant from creating excessive pods.

**Reliability:**
-   **Idempotency:** The provisioning logic checks for existing releases before installing. If a step fails, the system marks the store as `Failed` and logs the error, allowing safe retries or cleanup.
-   **Health Checks:** Kubernetes Liveness and Readiness probes ensure traffic only goes to healthy pods. If a WordPress instance crashes, K8s restarts it automatically.

---

## 3. Security Posture

**Secret Handling:**
-   **Auto-Generation:** Database and Admin passwords are generated cryptographically (using Python's `secrets` module) inside the orchestrator.
-   **K8s Secrets:** Credentials are injected directly into Kubernetes `Secret` objects. They are never exposed in the API response or stored in plain text in the main database (only references or non-sensitive data).

**Least Privilege (RBAC):**
-   The Backend ServiceAccount has specific permissions (create namespace, install release) but cannot access cluster-admin functions like modifying nodes or system components.

**Network Security:**
-   **Internal-Only DB:** The MariaDB database is not exposed via Ingress. Only the WordPress pod in the *same namespace* can talk to it (`ClusterIP`).
-   **Public Façade:** Only the WordPress HTTP/HTTPS port is exposed via Ingress.

---

## 4. Horizontal Scaling Plan

**Control Plane Scaling:**
-   **Stateless API:** The FastAPI backend is stateless. We can scale it horizontally (add more replicas) using a standard Kubernetes HorizontalPodAutoscaler (HPA) based on CPU/Memory usage.
-   **Orchestrator:** The background worker can be decoupled into a separate deployment if load increases, processing a shared job queue (e.g., Redis/Celery) to handle thousands of concurrent provisioning requests.

**Data Plane Scaling (Provisioning Throughput):**
-   **Helm Concurrency:** Helm installs are independent. K8s API server handles the concurrency. To scale this, we'd increase the API server capacity and Controller Manager replicas.
-   **Node Autoscaling:** We would use Cluster Autoscaler to add more Worker Nodes as new stores request more CPU/Memory capacity.

**Stateful Constraints:**
-   The databases (MariaDB) are stateful and harder to scale horizontally. For a massive scale, we would move from "DB-per-pod" to a managed database service (e.g., Cloud SQL) or a shared Operator-managed database cluster with logical database isolation per tenant.

---

## 5. Abuse Prevention & Guardrails

**Rate Limiting:**
-   **API Level:** Implemented `slowapi` on the backend to limit requests (e.g., 5 store creations per minute per IP) to prevent spam/DoS attacks on the provisioning engine.

**Blast Radius Controls:**
-   **Max Stores Per User:** A hard limit (quota) is enforced in the `create_store` logic (e.g., max 5 active stores) to prevent resource exhaustion.
-   **Timeouts:** Helm operations have strict timeouts (5 mins). If provisioning hangs, it's auto-cancelled to free up worker threads.

**Audit Logging:**
-   Every "Create" and "Delete" action is recorded in an immutable `audit_log` table with timestamps, resource IDs, and status outcomes for compliance and debugging.

---

## 6. Local to Production (VPS) Story

**Local (k3d/Docker):**
-   **Ingress:** Uses `localhost` or `*.k8s.local` with `/etc/hosts` mapping.
-   **Storage:** Uses local path provisioner (`k3d` default storage class).
-   **Values:** `values-local.yaml` disables persistence or uses smaller limits for speed.

**Production (VPS/Cloud):**
-   **Ingress:** Switch to a real Ingress Controller (Nginx/Traefik) with a real domain (e.g., `*.urumi.platform.com`) and Let's Encrypt for automatic TLS (HTTPS).
-   **Storage:** Switch Helm values to use `longhorn` or Cloud Provider Storage (EBS/GP3) for durability.
-   **Operations:**
    -   **Upgrades:** Use `helm upgrade` to patch WordPress versions across all tenants without downtime (rolling update).
    -   **Backups:** Use Velero to backup namespaces (PVCs + resources) to S3.

