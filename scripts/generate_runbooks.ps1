$docs_dir = "C:\Casualcast AI\deployment\docs\runbooks"

if (-not (Test-Path $docs_dir)) {
    New-Item -ItemType Directory -Path $docs_dir -Force | Out-Null
}

$ha_doc = @"
# High Availability (HA) Guide
- Backend is scaled to multiple replicas using HPA.
- PostgreSQL should be deployed using Patroni for HA.
- Redis should be deployed in Sentinel or Cluster mode.
- Nginx Ingress handles load balancing.
"@
Set-Content -Path "$docs_dir\ha_architecture.md" -Value $ha_doc

$dr_playbook = @"
# Disaster Recovery Playbook
## Database Failure
1. Identify the point of failure.
2. If primary is down, promote replica.
3. If data is corrupted, run the restore script: `./scripts/restore/restore.sh <date>`

## Kubernetes Cluster Failure
1. Spin up a new cluster.
2. Re-apply base manifests and overlays using Kustomize.
3. Restore database from off-site backup.
"@
Set-Content -Path "$docs_dir\dr_playbook.md" -Value $dr_playbook

$compliance_runbook = @"
# Compliance Runbook
## Access Reviews
- Perform quarterly access reviews via the Compliance Dashboard.
- Ensure terminated employees are deactivated immediately.

## Audit Logs
- Audit logs are immutable and archived to WORM storage every 24 hours.
- Alerts are configured for privilege escalation attempts.

## Data Governance
- PII must be masked.
- Ensure all datasets have a governance classification.
"@
Set-Content -Path "$docs_dir\compliance_runbook.md" -Value $compliance_runbook
