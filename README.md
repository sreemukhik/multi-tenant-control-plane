# Urumi Store Platform

Start-to-finish automated WooCommerce provisioning on Kubernetes.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

## Quick Start

### Prerequisites
- Docker
- k3d
- Helm
- kubectl

### 1. Setup Local Cluster
```bash
./scripts/setup-local.sh
```

### 2. Access
Add the following to your `/etc/hosts` (Unix) or `C:\Windows\System32\drivers\etc\hosts`:
```
127.0.0.1 dashboard.k8s.local api.k8s.local
```

Visit: [http://dashboard.k8s.local](http://dashboard.k8s.local)

### 3. Usage
1. Click "Create Store"
2. Enter a name (e.g. `test-store`)
3. Wait for provisioning (approx 2-3 mins)
4. Use the provided Admin/Storefront URLs.

## Project Structure
- `backend/`: FastAPI control plane
- `frontend/`: React dashboard
- `helm/`: Helm charts for Platform and Stores
