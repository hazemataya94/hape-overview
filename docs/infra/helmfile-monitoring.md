# Helmfile Monitoring Stack

## Purpose
Document local monitoring stack deployment through Helmfile.

## Helmfile definition
- File: `infrastructure/kubernetes/helmfile.yaml`
- Context: `kind-hape`
- Release: `kube-prometheus-stack`
- Values: `infrastructure/kubernetes/helm-values/kube-prometheus-stack-values.yaml`

## Deploy command
```bash
make helmfile-sync
```

## Current behavior
- Creates monitoring namespace as needed.
- Installs Prometheus Operator stack with local-focused settings.
- Uses a reduced set of default rules and disables control-plane component scrapers that are not useful for this local setup.

## Validation steps
1. Check release status:
   ```bash
   helm -n monitoring list
   ```
2. Check core pods:
   ```bash
   kubectl -n monitoring get pods
   ```
3. Check Prometheus service:
   ```bash
   kubectl -n monitoring get svc | grep prometheus
   ```

## Related files
- `infrastructure/kubernetes/helmfile.yaml`
- `infrastructure/kubernetes/helm-values/kube-prometheus-stack-values.yaml`
- `infrastructure/kubernetes/README.md`
