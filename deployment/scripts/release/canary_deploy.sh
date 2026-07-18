#!/bin/bash
set -e

echo "Starting Canary Deployment..."
# Apply canary
kubectl apply -f k8s/canary-deployment.yaml

echo "Waiting for Canary to be ready..."
kubectl rollout status deployment/backend-canary

echo "Canary deployed. Monitor metrics before full rollout."
