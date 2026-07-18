$release_dir = "C:\Casualcast AI\deployment\scripts\release"

if (-not (Test-Path $release_dir)) {
    New-Item -ItemType Directory -Path $release_dir -Force | Out-Null
}

# Blue-Green Deployment Script
$blueGreen = @"
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
"@
Set-Content -Path "$release_dir\blue_green_deploy.sh" -Value $blueGreen

# Canary Deployment Script
$canary = @"
#!/bin/bash
set -e

echo "Starting Canary Deployment..."
# Apply canary
kubectl apply -f k8s/canary-deployment.yaml

echo "Waiting for Canary to be ready..."
kubectl rollout status deployment/backend-canary

echo "Canary deployed. Monitor metrics before full rollout."
"@
Set-Content -Path "$release_dir\canary_deploy.sh" -Value $canary

# Rollback Script
$rollback = @"
#!/bin/bash
set -e

echo "Rolling back deployment..."
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/frontend

echo "Rollback initiated. Waiting for status..."
kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend

echo "Rollback complete."
"@
Set-Content -Path "$release_dir\rollback.sh" -Value $rollback
