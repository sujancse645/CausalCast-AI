$base_dir = "C:\Casualcast AI\deployment\kubernetes\base"

New-Item -ItemType Directory -Path "$base_dir\networking" -Force | Out-Null
New-Item -ItemType Directory -Path "$base_dir\security" -Force | Out-Null

# Ingress
$ingress = @"
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: causalcast-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - causalcast.example.com
    secretName: causalcast-tls
  rules:
  - host: causalcast.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
"@
Set-Content -Path "$base_dir\networking\ingress.yaml" -Value $ingress

# NetworkPolicy
$netpol = @"
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
"@
Set-Content -Path "$base_dir\networking\networkpolicy.yaml" -Value $netpol

# RBAC and ServiceAccount
$rbac = @"
apiVersion: v1
kind: ServiceAccount
metadata:
  name: causalcast-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: causalcast-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: causalcast-rolebinding
subjects:
- kind: ServiceAccount
  name: causalcast-sa
roleRef:
  kind: Role
  name: causalcast-role
  apiGroup: rbac.authorization.k8s.io
"@
Set-Content -Path "$base_dir\security\rbac.yaml" -Value $rbac

# PodDisruptionBudget
$pdb = @"
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: backend
"@
Set-Content -Path "$base_dir\security\pdb.yaml" -Value $pdb

# Add to kustomization.yaml
Add-Content "$base_dir\kustomization.yaml" "  - networking/ingress.yaml"
Add-Content "$base_dir\kustomization.yaml" "  - networking/networkpolicy.yaml"
Add-Content "$base_dir\kustomization.yaml" "  - security/rbac.yaml"
Add-Content "$base_dir\kustomization.yaml" "  - security/pdb.yaml"
