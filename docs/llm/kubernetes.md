# HAPE Kubernetes Rules

Apply these rules when creating or updating Kubernetes manifests in this repository.

## Resource limits
- Hard rule: Do not add CPU values under `resources.limits` in Kubernetes manifests.
