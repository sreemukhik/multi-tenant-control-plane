#!/bin/bash
set -e

# This script sets up k3s + platform on a Google Cloud Free Tier VM
# Assumes:
# - VM is already created (e.g. e2-micro/small, Ubuntu 22.04)
# - External IP is assigned
# - Firewall allows ports 80, 443, 22

VM_EXTERNAL_IP=$1
DOMAIN=$2

if [ -z "$VM_EXTERNAL_IP" ] || [ -z "$DOMAIN" ]; then
  echo "Usage: ./setup-prod.sh <VM_EXTERNAL_IP> <DOMAIN>"
  exit 1
fi

echo "🚀 Installing k3s on Google Cloud VM..."
ssh -o StrictHostKeyChecking=no root@$VM_EXTERNAL_IP 'curl -sfL https://get.k3s.io | sh -'

echo "📥 Copying kubeconfig..."
scp -o StrictHostKeyChecking=no root@$VM_EXTERNAL_IP:/etc/rancher/k3s/k3s.yaml ~/.kube/config-vps
sed -i "s/127.0.0.1/$VM_EXTERNAL_IP/g" ~/.kube/config-vps
export KUBECONFIG=~/.kube/config-vps

echo "🔒 Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

echo "⏳ Waiting for cert-manager..."
kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager

echo "📦 Installing platform..."
helm upgrade --install urumi-platform ./helm/platform \
  -f ./helm/platform/values-prod.yaml \
  --set global.baseDomain=$DOMAIN \
  --namespace urumi-platform \
  --create-namespace \
  --wait

echo "✅ Platform deployed!"
echo "Dashboard via HTTPS: https://dashboard.$DOMAIN"
echo "API via HTTPS: https://api.$DOMAIN"
