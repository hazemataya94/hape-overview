# Kube Agent Kubernetes Test Fixtures

## Purpose
This directory contains Kubernetes fixture manifests for `kube-agent` functional tests.
Tests apply these fixtures with `kubectl apply -k` on a local `kind` cluster.

## Files
- `kustomization.yaml`
- `namespaces.yaml`
- `deployments.yaml`

## Notes
- Fixtures are local-only and do not require EKS.
- Keep fixture changes aligned with assertions in `tests/kube_agent/test_kube_agent_functional.py`.
