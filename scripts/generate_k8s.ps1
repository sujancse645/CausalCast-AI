$base_dir = "C:\Casualcast AI\deployment\kubernetes\base"

$dirs = @(
    "$base_dir\backend",
    "$base_dir\frontend",
    "$base_dir\workers",
    "$base_dir\scheduler",
    "$base_dir\postgres",
    "$base_dir\redis",
    "$base_dir\ingress",
    "$base_dir\monitoring",
    "$base_dir\otel",
    "$base_dir\jobs",
    "$base_dir\storage"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Backend Deployment
$backendDeployment = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: backend
spec:
  replicas: 2
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
        image: causalcast/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: backend-config
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1024Mi
"@
Set-Content -Path "$base_dir\backend\deployment.yaml" -Value $backendDeployment

# Backend Service
$backendService = @"
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
"@
Set-Content -Path "$base_dir\backend\service.yaml" -Value $backendService

# Frontend Deployment
$frontendDeployment = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: causalcast/frontend:latest
        ports:
        - containerPort: 3000
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
"@
Set-Content -Path "$base_dir\frontend\deployment.yaml" -Value $frontendDeployment

# Frontend Service
$frontendService = @"
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
"@
Set-Content -Path "$base_dir\frontend\service.yaml" -Value $frontendService

# Redis Deployment
$redisDeployment = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
"@
Set-Content -Path "$base_dir\redis\deployment.yaml" -Value $redisDeployment

# Redis Service
$redisService = @"
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
"@
Set-Content -Path "$base_dir\redis\service.yaml" -Value $redisService

# Postgres StatefulSet
$postgresSts = @"
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  labels:
    app: postgres
spec:
  serviceName: "postgres"
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: "causalcast"
        - name: POSTGRES_PASSWORD
          value: "causalcast"
        - name: POSTGRES_DB
          value: "causalcast"
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
"@
Set-Content -Path "$base_dir\postgres\statefulset.yaml" -Value $postgresSts

# Postgres Service
$postgresService = @"
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
"@
Set-Content -Path "$base_dir\postgres\service.yaml" -Value $postgresService

# Worker Deployment
$workerDeployment = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  labels:
    app: worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: causalcast/backend:latest
        command: ["celery", "-A", "app.worker", "worker", "-l", "info"]
        envFrom:
        - configMapRef:
            name: backend-config
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
"@
Set-Content -Path "$base_dir\workers\deployment.yaml" -Value $workerDeployment

# Scheduler Deployment
$schedulerDeployment = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler
  labels:
    app: scheduler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: scheduler
  template:
    metadata:
      labels:
        app: scheduler
    spec:
      containers:
      - name: scheduler
        image: causalcast/backend:latest
        command: ["celery", "-A", "app.worker", "beat", "-l", "info"]
        envFrom:
        - configMapRef:
            name: backend-config
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 512Mi
"@
Set-Content -Path "$base_dir\scheduler\deployment.yaml" -Value $schedulerDeployment

# Generate kustomization.yaml files
$kustomizationBase = @"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - backend/deployment.yaml
  - backend/service.yaml
  - frontend/deployment.yaml
  - frontend/service.yaml
  - redis/deployment.yaml
  - redis/service.yaml
  - postgres/statefulset.yaml
  - postgres/service.yaml
  - workers/deployment.yaml
  - scheduler/deployment.yaml
"@
Set-Content -Path "$base_dir\kustomization.yaml" -Value $kustomizationBase
