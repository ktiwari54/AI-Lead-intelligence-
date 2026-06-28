# 02 — Kubernetes Architecture (Local Practice)

## Scope

Kubernetes is **optional** for this platform. Daily development uses Docker Compose. This document covers **local-only** Kubernetes with k3d or minikube for learning, integration testing, and future migration planning — no managed K8s clusters required.

## When to Use K8s vs Docker Compose

| Scenario | Recommendation |
|----------|----------------|
| Local dev, debugging | Docker Compose (`docker-compose.yml`) |
| CI smoke tests | Docker Compose (`.github/workflows/free-stack-smoke.yml`) |
| Learning K8s manifests | k3d or minikube |
| Multi-replica API testing | k3d with `kubectl scale` |
| Production (small team) | Docker Compose or single-node k3s on owned hardware |

## Target Architecture (Local Cluster)

```
┌─────────────────────────────────────────────────────────┐
│  k3d cluster: ai-lead-intel                           │
│                                                         │
│  Namespace: ai-lead-dev                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Deployment  │  │ Deployment  │  │ Deployment  │    │
│  │ api (x2)    │  │ worker (x2) │  │ beat (x1)   │    │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘    │
│         │                │                              │
│  ┌──────▼────────────────▼──────────────────────┐      │
│  │ Service: api (ClusterIP :8000)               │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
│  StatefulSet: postgres   PVC: pgdata                    │
│  Deployment: redis                                      │
│  Deployment: opensearch                                   │
│                                                         │
│  Ingress (optional): port-forward or k3d LB             │
└─────────────────────────────────────────────────────────┘
```

## k3d Setup (Windows + WSL2 or native)

### Install

```powershell
# Chocolatey or scoop
choco install k3d

# Or via script (check k3d.io for latest)
winget install k3d
```

### Create Cluster

```powershell
k3d cluster create ai-lead-intel `
  --agents 2 `
  --port "8000:30080@loadbalancer" `
  --port "3000:30000@loadbalancer" `
  --volume "C:\Users\PC\AI-Lead-intelligence-\:/workspace@all"
```

### Load Local Image

```powershell
cd C:\Users\PC\AI-Lead-intelligence-
docker build -t ai-lead-intelligence:local .
k3d image import ai-lead-intelligence:local -c ai-lead-intel
```

## minikube Alternative

```powershell
minikube start --cpus 4 --memory 8192 --driver=docker
minikube addons enable ingress
eval $(minikube docker-env)   # Linux/WSL
docker build -t ai-lead-intelligence:local .
```

## Sample Manifests (Reference)

Create under `infra/k8s/local/` (not required for Compose workflow):

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-lead-dev
```

### API Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: ai-lead-dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: ai-lead-intelligence:local
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: ai-lead-env
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

### Worker Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: ai-lead-dev
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
          image: ai-lead-intelligence:local
          command: ["celery", "-A", "backend.workers.celery_app", "worker", "--loglevel=info"]
          envFrom:
            - secretRef:
                name: ai-lead-env
```

## Secrets from .env

```powershell
kubectl create namespace ai-lead-dev
kubectl create secret generic ai-lead-env `
  --from-env-file=.env `
  -n ai-lead-dev
```

Never commit `.env` to git. Use `.env.example` as template.

## Port Forwarding (Quick Access)

```powershell
kubectl port-forward svc/api 8000:8000 -n ai-lead-dev
curl http://localhost:8000/health
```

## Horizontal Pod Autoscaler (Future)

When running on a real cluster with metrics-server (included in k3d):

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: ai-lead-dev
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Requires Prometheus Adapter or metrics-server — both open source.

## Monitoring in K8s

Reuse existing Prometheus/Grafana configs from `infra/monitoring/`. Options:

1. **Helm** (free): `prometheus-community/kube-prometheus-stack`
2. **Compose side-by-side**: run monitoring in Compose, scrape via `host.docker.internal`

For local practice, keeping monitoring in Compose is simpler.

## CI Integration (Optional)

Add a GitHub Actions job using [helm/kind-action](https://github.com/marketplace/actions/kind-cluster) or k3d — free on `ubuntu-latest`. Start with the existing `free-stack-smoke.yml` before adding K8s jobs.

## Tear Down

```powershell
k3d cluster delete ai-lead-intel
# or
minikube delete
```

## Related Documents

- [03-docker-standards.md](./03-docker-standards.md) — image used by K8s pods
- [14-scaling-strategy.md](./14-scaling-strategy.md) — Compose scale vs HPA
- [04-cicd-pipeline.md](./04-cicd-pipeline.md) — image build in CI