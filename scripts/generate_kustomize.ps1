$overlays_dir = "C:\Casualcast AI\deployment\kubernetes\overlays"

$envs = @("development", "staging", "production", "gpu")

foreach ($env in $envs) {
    $dir = "$overlays_dir\$env"
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Development overlay
$devKustomization = @"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: dev-
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 1
    target:
      kind: Deployment
      name: backend
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 1
    target:
      kind: Deployment
      name: frontend
"@
Set-Content -Path "$overlays_dir\development\kustomization.yaml" -Value $devKustomization

# Staging overlay
$stagingKustomization = @"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: staging-
"@
Set-Content -Path "$overlays_dir\staging\kustomization.yaml" -Value $stagingKustomization

# Production overlay
$prodKustomization = @"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: prod-
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
    target:
      kind: Deployment
      name: backend
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
    target:
      kind: Deployment
      name: frontend
"@
Set-Content -Path "$overlays_dir\production\kustomization.yaml" -Value $prodKustomization

# GPU overlay
$gpuKustomization = @"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources/limits/nvidia.com~1gpu
        value: "1"
    target:
      kind: Deployment
      name: workers
"@
Set-Content -Path "$overlays_dir\gpu\kustomization.yaml" -Value $gpuKustomization
