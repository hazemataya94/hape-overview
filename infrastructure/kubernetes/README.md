# Kubernetes Local Environment

## Purpose
This directory defines the local Kubernetes environment for HAPE.
Use it to create the `kind` cluster and bootstrap cluster tooling with Helmfile.
The `eks-deployment-cost/` directory is a kustomize base used as test fixtures for `eks-deployment-cost` functional tests.
The `kube-agent/` directory is a kustomize base used as test fixtures for `kube-agent` functional tests.
The `exporters/` directory contains exporter deployment manifests for local Kubernetes.
The `aws-credentials/` directory contains local secret generation for AWS credentials used by exporters.

## Prerequisites
- `kind`
- `kubectl`
- `helm`
- `helmfile`

## Create the local cluster
```bash
make kind-up
```

## Install tools with Helmfile
```bash
make helmfile-sync
```

## Delete the local cluster
```bash
make kind-down
```
