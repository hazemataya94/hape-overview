# Kubernetes Local Environment

## Purpose
This directory defines the local Kubernetes environment for HAPE.
Use it to create the `kind` cluster and bootstrap cluster tooling with Helmfile.
The `eks-deployment-cost/manifests/` files are test fixtures for `eks-deployment-cost` functional tests.

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
helmfile -f infrastructure/kubernetes/helmfile.yaml sync
```

## Delete the local cluster
```bash
make kind-down
```
