# Kube Agent Fixtures

## Purpose
Document Kubernetes fixture manifests used by `kube-agent` functional tests on local `kind`.

## Fixture files
- `infrastructure/kubernetes/kube-agent/kustomization.yaml`
- `infrastructure/kubernetes/kube-agent/namespaces.yaml`
- `infrastructure/kubernetes/kube-agent/deployments.yaml`

## How fixtures are used
- Tests apply these manifests to create a deterministic workload in namespace `kube-agent-test`.
- The workload provides stable pod status, logs, events, and owner references for investigation assertions.
- The fixture does not require EKS and does not use billable cloud infrastructure.

## Local validation
Apply fixtures:

```bash
kubectl apply -k infrastructure/kubernetes/kube-agent
```

Inspect workloads:

```bash
kubectl get deploy,pods -n kube-agent-test
```

Cleanup:

```bash
kubectl delete -k infrastructure/kubernetes/kube-agent
```

## Related files
- `infrastructure/kubernetes/kube-agent/README.md`
- `tests/kube_agent/README.md`
- `tests/kube_agent/test_kube_agent_functional.py`
