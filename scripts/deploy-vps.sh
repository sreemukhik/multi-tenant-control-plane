#!/bin/bash
set -e

# --- CONFIGURATION ---
PUBLIC_IP=$1
DOMAIN=${2:-"$PUBLIC_IP.nip.io"}

if [ -z "$PUBLIC_IP" ]; then
    echo "Usage: ./deploy-vps.sh <PUBLIC_IP> [DOMAIN]"
    echo "Example: ./deploy-vps.sh 1.2.3.4"
    exit 1
fi

echo "🚀 Starting Automated Urumi VPS Deployment on $DOMAIN..."

# 1. Install k3s
if ! command -v k3s &> /dev/null; then
    echo "Installing k3s..."
    curl -sfL https://get.k3s.io | sh -
    mkdir -p ~/.kube
    sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    sudo chown $USER:$USER ~/.kube/config
fi

# 2. Install Helm
if ! command -v helm &> /dev/null; then
    echo "Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# 3. Build & Import Images (Local Build on VPS to save time)
echo "Building Platform Images..."
docker build -t urumi-platform-api:vps ./backend
docker build -t urumi-dashboard:vps ./frontend

# Export and Import to k3s containerd
echo "Importing images into k3s..."
docker save urumi-platform-api:vps | sudo k3s ctr images import -
docker save urumi-dashboard:vps | sudo k3s ctr images import -

# 4. Prepare VPS Values
cat <<EOF > helm/platform/values-vps.yaml
global:
  environment: vps
  baseDomain: "$DOMAIN"

platform:
  api:
    image:
      repository: urumi-platform-api
      tag: vps
      pullPolicy: Never
    replicas: 2
    env:
      DATABASE_URL: "postgresql+asyncpg://urumi:urumi123@platform-db:5432/urumi"
  
  dashboard:
    image:
      repository: urumi-dashboard
      tag: vps
      pullPolicy: Never
    replicas: 2

ingress:
  enabled: true
  className: traefik
  hosts:
    - host: "dashboard.$DOMAIN"
      paths:
        - path: /
          service: urumi-dashboard
    - host: "api.$DOMAIN"
      paths:
        - path: /
          service: urumi-platform-api
EOF

# 5. Deploy Platform
echo "Installing Urumi Platform via Helm..."
helm upgrade --install urumi-platform ./helm/platform \
    --namespace urumi-platform \
    --create-namespace \
    --values helm/platform/values-vps.yaml \
    --wait

echo "------------------------------------------------"
echo "✅ DEPLOYMENT COMPLETE!"
echo "Dashboard: http://dashboard.$DOMAIN"
echo "API: http://api.$DOMAIN"
echo "------------------------------------------------"
echo "Note: If using AWS/GCP, ensure ports 80/443 are open in Security Groups!"
