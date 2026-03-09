# EKS Deployment Cost Functional Tests (Local kind)

## Purpose
This test suite validates `eks-deployment-cost` report generation against a local Kubernetes API.
It does not create or require an EKS cluster.

## Prerequisites
- `kind` installed locally.
- `kubectl` installed locally.
- Python dependencies installed in `.venv`.

## Cluster shape
- 1 control-plane node.
- 4 worker nodes.
- Worker nodes include labels that simulate EKS metadata such as:
  - `eks.amazonaws.com/nodegroup`
  - `node.kubernetes.io/instance-type`
  - `topology.kubernetes.io/zone`

## Files
- `kind.yaml` cluster definition.
- `manifests/` test namespaces and workloads.
- `conftest.py` cluster and manifest fixtures.
- `test_eks_deployment_cost_functional.py` end-to-end local functional test.

## Start KIND Cluster
```bash
kind create cluster --config tests/eks-deployment-cost/kind.yaml
```

## Run
```bash
HAPE_RUN_KIND_FUNCTIONAL_TESTS=1 python -m pytest tests/eks-deployment-cost -q -s
```
