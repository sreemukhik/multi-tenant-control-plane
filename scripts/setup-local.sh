#!/bin/bash
set -e

echo "🚀 Setting up Urumi Platform (Local)..."

# 1. Create k3d cluster
if k3d cluster list | grep -q "urumi-cluster"; then
    echo "Cluster already exists, skipping creation."
else
    echo "Creating k3d cluster..."
    k3d cluster create urumi-cluster \
        --api-port 6443 \
        -p "80:80@loadbalancer" \
        -p "443:443@loadbalancer" \
        --k3s-arg "--disable=traefik@server:0" # Disable default traefik to install our own or use chart's
        # Actually platform chart uses Traefik too? Spec says "Ingress Controller: Traefik (bundled with k3s)"
        # So we should KEEP default traefik.
        # Removing the disable arg.
fi

# 2. Build images (Mocking build for now, or use placeholder)
echo "Building component images..."
docker build -t urumi-platform-api:latest ./backend
docker build -t urumi-dashboard:latest ./frontend # This assumes Dockerfile in frontend builds nginx serving static

# Import images to k3d
echo "Importing images to k3d..."
k3d image import urumi-platform-api:latest -c urumi-cluster
k3d image import urumi-dashboard:latest -c urumi-cluster


# 3. Install Platform Chart
echo "Installing Platform Chart..."
helm upgrade --install urumi-platform ./helm/platform \
    --namespace urumi-platform \
    --create-namespace \
    --values ./helm/platform/values-local.yaml \
    --wait

echo "✅ Platform installed!"
echo "Add to /etc/hosts: 127.0.0.1 dashboard.k8s.local api.k8s.local"
