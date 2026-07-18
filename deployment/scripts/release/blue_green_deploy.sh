#!/bin/bash
set -e

echo "Starting Blue-Green Deployment..."
# Create green deployment
kubectl apply -f k8s/green-deployment.yaml

echo "Waiting for Green deployment to be ready..."
kubectl rollout status deployment/backend-green

echo "Switching traffic to Green deployment..."
kubectl patch service backend -p '{"spec":{"selector":{"version":"green"}}}'

echo "Scaling down Blue deployment..."
kubectl scale deployment/backend-blue --replicas=0

echo "Blue-Green Deployment successful."
