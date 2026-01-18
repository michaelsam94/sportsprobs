# Kubernetes Deployment

## Prerequisites

- Kubernetes cluster
- kubectl configured
- Docker image pushed to registry

## Deployment Steps

1. **Create secrets:**
```bash
kubectl create secret generic sports-secrets \
  --from-literal=database-url='postgresql+asyncpg://user:pass@host:5432/db' \
  --from-literal=redis-url='redis://host:6379/0' \
  --from-literal=secret-key='your-secret-key' \
  --from-literal=admin-token='your-admin-token'
```

2. **Deploy application:**
```bash
kubectl apply -f deployment.yaml
```

3. **Check status:**
```bash
kubectl get pods
kubectl get services
```

4. **View logs:**
```bash
kubectl logs -f deployment/sports-api
```

## Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment sports-api --replicas=5
```

