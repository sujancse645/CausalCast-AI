#!/bin/bash
set -e

echo "Rolling back deployment..."
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/frontend

echo "Rollback initiated. Waiting for status..."
kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend

echo "Rollback complete."
