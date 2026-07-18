$base_dir = "C:\Casualcast AI\deployment"

# Monitoring manifests
$mon_dir = "$base_dir\kubernetes\base\monitoring"
if (-not (Test-Path $mon_dir)) { New-Item -ItemType Directory -Path $mon_dir -Force | Out-Null }

$prometheus = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
"@
Set-Content -Path "$mon_dir\prometheus.yaml" -Value $prometheus

$grafana = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
"@
Set-Content -Path "$mon_dir\grafana.yaml" -Value $grafana

# OTEL Collector
$otel_dir = "$base_dir\kubernetes\base\otel"
if (-not (Test-Path $otel_dir)) { New-Item -ItemType Directory -Path $otel_dir -Force | Out-Null }

$otel = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        ports:
        - containerPort: 4317
        - containerPort: 4318
"@
Set-Content -Path "$otel_dir\otel-collector.yaml" -Value $otel

# Backup & Restore Scripts
$scripts_dir = "$base_dir\scripts"
if (-not (Test-Path "$scripts_dir\backup")) { New-Item -ItemType Directory -Path "$scripts_dir\backup" -Force | Out-Null }
if (-not (Test-Path "$scripts_dir\restore")) { New-Item -ItemType Directory -Path "$scripts_dir\restore" -Force | Out-Null }

$backup = @"
#!/bin/bash
echo "Starting database backup..."
pg_dump -U causalcast causalcast > /backup/causalcast_backup_`$(date +%F).sql
echo "Backup complete."
"@
Set-Content -Path "$scripts_dir\backup\backup.sh" -Value $backup

$restore = @"
#!/bin/bash
echo "Starting database restore..."
psql -U causalcast causalcast < /backup/causalcast_backup_$1.sql
echo "Restore complete."
"@
Set-Content -Path "$scripts_dir\restore\restore.sh" -Value $restore

# Add to kustomization.yaml
Add-Content "$base_dir\kubernetes\base\kustomization.yaml" "  - monitoring/prometheus.yaml"
Add-Content "$base_dir\kubernetes\base\kustomization.yaml" "  - monitoring/grafana.yaml"
Add-Content "$base_dir\kubernetes\base\kustomization.yaml" "  - otel/otel-collector.yaml"
