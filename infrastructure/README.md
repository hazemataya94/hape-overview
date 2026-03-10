# Infrastructure

## Purpose
This directory contains local infrastructure setup assets for HAPE development and testing.
It starts with local Kubernetes setup on `kind` and reserves space for future Terraform assets.

## Directory layout
- `kubernetes/`: local Kubernetes cluster setup, Helmfile definitions, and bootstrap manifests.
- `terraform/`: reserved for future Terraform modules and environments.

## Current scope
- Create and manage a local `kind` cluster for development and functional tests.
- Install local cluster tools with Helmfile.

## Future scope
- Add Terraform structure and modules under `terraform/`.
