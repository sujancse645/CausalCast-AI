# Disaster Recovery Playbook
## Database Failure
1. Identify the point of failure.
2. If primary is down, promote replica.
3. If data is corrupted, run the restore script: ./scripts/restore/restore.sh <date>

## Kubernetes Cluster Failure
1. Spin up a new cluster.
2. Re-apply base manifests and overlays using Kustomize.
3. Restore database from off-site backup.
