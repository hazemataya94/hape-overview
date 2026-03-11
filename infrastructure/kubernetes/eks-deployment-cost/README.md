# EKS Deployment Cost Kubernetes Test Fixtures

## Purpose
This directory contains Kubernetes fixture manifests used by `eks-deployment-cost` functional tests.
These files are test fixtures and are applied by `tests/eks-deployment-cost/conftest.py` with `kubectl apply -k`.

## Files
- `kustomization.yaml`
- `namespaces.yaml`
- `deployments.yaml`
- `statefulsets.yaml`
