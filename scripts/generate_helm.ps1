$helm_dir = "C:\Casualcast AI\deployment\helm\causalcast"

$dirs = @(
    "$helm_dir\templates\backend",
    "$helm_dir\templates\frontend",
    "$helm_dir\templates\workers",
    "$helm_dir\templates\scheduler",
    "$helm_dir\templates\monitoring",
    "$helm_dir\templates\jobs",
    "$helm_dir\templates\networking",
    "$helm_dir\templates\storage"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Chart.yaml
$chartYaml = @"
apiVersion: v2
name: causalcast
description: A Helm chart for CausalCast AI Enterprise Deployment
type: application
version: 0.1.0
appVersion: "1.0.0"
"@
Set-Content -Path "$helm_dir\Chart.yaml" -Value $chartYaml

# values.yaml
$valuesYaml = @"
backend:
  replicaCount: 2
  image:
    repository: causalcast/backend
    pullPolicy: IfNotPresent
    tag: "latest"
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1024Mi

frontend:
  replicaCount: 2
  image:
    repository: causalcast/frontend
    pullPolicy: IfNotPresent
    tag: "latest"

workers:
  replicaCount: 2

scheduler:
  replicaCount: 1

redis:
  enabled: true
  
postgres:
  enabled: true

ingress:
  enabled: false
"@
Set-Content -Path "$helm_dir\values.yaml" -Value $valuesYaml

# values-development.yaml
$valuesDevYaml = @"
backend:
  replicaCount: 1
frontend:
  replicaCount: 1
workers:
  replicaCount: 1
"@
Set-Content -Path "$helm_dir\values-development.yaml" -Value $valuesDevYaml

# values-production.yaml
$valuesProdYaml = @"
backend:
  replicaCount: 3
frontend:
  replicaCount: 3
workers:
  replicaCount: 3
ingress:
  enabled: true
"@
Set-Content -Path "$helm_dir\values-production.yaml" -Value $valuesProdYaml

# templates/_helpers.tpl
$helpersTpl = @"
{{- define "causalcast.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
"@
Set-Content -Path "$helm_dir\templates\_helpers.tpl" -Value $helpersTpl

# templates/backend/deployment.yaml
$backendTpl = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "causalcast.fullname" . }}-backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          ports:
            - containerPort: 8000
"@
Set-Content -Path "$helm_dir\templates\backend\deployment.yaml" -Value $backendTpl
