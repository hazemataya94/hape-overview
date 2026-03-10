# Makefile Documentation

## Purpose
Document all `Makefile` variables and targets in one place.

## Variables
- `PYTHON` (default: `python`)
- `VERSION_FILE` (default: `VERSION`)
- `INSTALL_PREFIX` (default: empty)
- `KIND_CLUSTER_NAME` (default: `hape`)
- `KIND_CONFIG_PATH` (default: `infrastructure/kubernetes/kind/cluster-config.yaml`)

## Targets
- `make help`: list available Make targets and descriptions.
- `make clean`: remove local build artifacts (`build`, `dist`, `*.egg-info`).
- `make bump-version`: increment patch version in `VERSION`.
- `make build`: bump version, then build wheel and source distribution.
- `make install`: install latest wheel from `dist/` with optional prefix.
- `make kind-up`: create local `kind` cluster when not already running.
- `make helmfile-sync`: sync Helmfile releases for local cluster tooling.
- `make kind-down`: delete local `kind` cluster when running.

## Common usage
Show available targets:

```bash
make help
```

Build package:

```bash
make build
```

Install latest wheel:

```bash
make install
```

Create local cluster:

```bash
make kind-up
```

Sync Helmfile releases:

```bash
make helmfile-sync
```

Delete local cluster:

```bash
make kind-down
```

## Validation steps
1. Run `make help` and verify listed targets match this document.
2. Run `make kind-up` and verify cluster exists with `kind get clusters`.
3. Run `make helmfile-sync` and verify Helm releases with `helm -n monitoring list`.
4. Run `make kind-down` and verify cluster is removed.
