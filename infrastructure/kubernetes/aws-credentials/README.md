# AWS Credentials Secret

## Purpose
This directory creates the `hape-aws-credentials` Kubernetes Secret used by the EKS deployment cost exporter.

## Prerequisite
Create a local credentials file in this directory:

```bash
cp ~/.aws/credentials infrastructure/kubernetes/aws-credentials/.aws-credentials
```

Do not commit `.aws-credentials`.

## Apply
```bash
make kustomize-apply infrastructure/kubernetes/aws-credentials
```

## Delete
```bash
make kustomize-delete infrastructure/kubernetes/aws-credentials
```
