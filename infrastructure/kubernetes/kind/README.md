# KIND Cluster Configuration

## Purpose
This directory contains local `kind` cluster configuration used by the `eks-deployment-cost` functional test suite.

## Contents
- `cluster-config.yaml`: local kind cluster topology used by tests.

## Usage
- Functional tests consume these files through test fixtures.
- Keep changes aligned with expectations in `tests/eks-deployment-cost/test_eks_deployment_cost_functional.py`.
