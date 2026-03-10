# EKS Deployment Cost Fixtures

## Purpose
Document Kubernetes fixture manifests used by `eks-deployment-cost` functional tests.

## Fixture files
- `infrastructure/kubernetes/eks-deployment-cost/manifests/namespaces.yaml`
- `infrastructure/kubernetes/eks-deployment-cost/manifests/deployments.yaml`
- `infrastructure/kubernetes/eks-deployment-cost/manifests/statefulsets.yaml`

## How fixtures are used
- Tests apply these manifests to create deterministic workloads in `cost-a` and `cost-b`.
- Deployments and StatefulSets include different request patterns (cpu-only, memory-only, both, or missing requests) to validate cost calculations and defaults.

## Local validation
Apply fixtures:

```bash
kubectl apply -f infrastructure/kubernetes/eks-deployment-cost/manifests/namespaces.yaml
kubectl apply -f infrastructure/kubernetes/eks-deployment-cost/manifests/deployments.yaml
kubectl apply -f infrastructure/kubernetes/eks-deployment-cost/manifests/statefulsets.yaml
```

Inspect workloads:

```bash
kubectl get deploy,statefulset -A | grep -E "cost-a|cost-b"
```

Cleanup:

```bash
kubectl delete ns cost-a cost-b
```

## Related files
- `infrastructure/kubernetes/eks-deployment-cost/README.md`
- `tests/eks-deployment-cost/README.md`
