$base_dir = "C:\Casualcast AI\deployment\kubernetes\base"

New-Item -ItemType Directory -Path "$base_dir\scaling" -Force | Out-Null

# HPA for backend
$hpa = @"
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"@
Set-Content -Path "$base_dir\scaling\hpa.yaml" -Value $hpa

# KEDA ScaledObject for workers
$keda = @"
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-scaler
spec:
  scaleTargetRef:
    name: worker
  minReplicaCount: 1
  maxReplicaCount: 20
  triggers:
  - type: redis
    metadata:
      address: redis:6379
      listName: celery
      listLength: "10"
"@
Set-Content -Path "$base_dir\scaling\keda.yaml" -Value $keda

# Add to kustomization.yaml
Add-Content "$base_dir\kustomization.yaml" "  - scaling/hpa.yaml"
Add-Content "$base_dir\kustomization.yaml" "  - scaling/keda.yaml"
