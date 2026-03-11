# Infrastructure Overview

## Purpose
Describe the infrastructure assets used by HAPE for local development and functional testing.

## Scope
- Local Kubernetes environment on `kind`.
- Local monitoring stack bootstrap with Helmfile.
- Functional test fixtures for `eks-deployment-cost`.
- Exporter runtime deployment manifests for local Kubernetes.
- Terraform placeholder for future infrastructure-as-code modules.

## Software architecture view
- `Makefile` orchestrates local infrastructure lifecycle commands.
- `infrastructure/kubernetes/kind/cluster-config.yaml` defines cluster topology and EKS-like labels.
- `infrastructure/kubernetes/helmfile.yaml` declares cluster add-ons and values sources.
- `infrastructure/kubernetes/eks-deployment-cost/` contains a kustomize base with deterministic functional test fixtures.
- `infrastructure/kubernetes/exporters/eks-deployment-cost/` contains a kustomize base for exporter deployment.

## System architecture view
- A local multi-node `kind` cluster simulates key EKS scheduling attributes with worker node labels.
- Monitoring components run inside the cluster via `kube-prometheus-stack`.
- Functional tests apply fixture manifests into test namespaces to validate cost-report behavior.

## Directory mapping
- `infrastructure/README.md`
- `infrastructure/kubernetes/README.md`
- `infrastructure/kubernetes/kind/README.md`
- `infrastructure/kubernetes/helmfile.yaml`
- `infrastructure/kubernetes/helm-values/kube-prometheus-stack-values.yaml`
- `infrastructure/kubernetes/eks-deployment-cost/README.md`
- `infrastructure/kubernetes/exporters/README.md`
- `infrastructure/kubernetes/exporters/eks-deployment-cost/kustomization.yaml`
- `infrastructure/terraform/README.md`

## Validation steps
1. Run `make kind-up`.
2. Run `make helmfile-sync`.
3. Verify namespaces:
   ```bash
   kubectl get ns cost-a cost-b
   ```
