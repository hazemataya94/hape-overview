# Local Kubernetes

## Purpose
Document how to create, inspect, and remove the local `kind` cluster used by HAPE development and tests.

## Inputs
- Cluster name: `hape` (default from `Makefile`).
- Cluster config: `infrastructure/kubernetes/kind/cluster-config.yaml`.

## Cluster topology
- 1 control-plane node.
- 4 worker nodes.
- Worker nodes include EKS-like labels for node group, instance type, and zone.

## Lifecycle commands
Create cluster:

```bash
make kind-up
```

Check cluster:

```bash
kubectl cluster-info
kubectl get nodes --show-labels
```

Delete cluster:

```bash
make kind-down
```

Before applying `infrastructure/kubernetes/aws-credentials`, create local file `infrastructure/kubernetes/aws-credentials/.aws-credentials` from your AWS credentials source.
```bash
cp ~/.aws/credentials infrastructure/kubernetes/aws-credentials/.aws-credentials
```

Deploy EKS deployment cost exporter:

```bash
make kustomize-apply infrastructure/kubernetes/aws-credentials
make kustomize-apply infrastructure/kubernetes/exporters/eks-deployment-cost
```

## Expected result
- `make kind-up` creates cluster `hape` when not already running.
- `make kind-down` deletes cluster `hape` when running.

## Related files
- `infrastructure/kubernetes/kind/cluster-config.yaml`
- `infrastructure/kubernetes/kind/README.md`
- `infrastructure/kubernetes/kube-agent/kustomization.yaml`
- `infrastructure/kubernetes/exporters/README.md`
- `infrastructure/kubernetes/exporters/eks-deployment-cost/kustomization.yaml`
- `Makefile`
