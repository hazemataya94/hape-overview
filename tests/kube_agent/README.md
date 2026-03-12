# Kube Agent Tests

## Purpose
This test suite validates `hape-kube-agent` trigger parsing, evidence normalization, deterministic checks, incident case building, memory behavior, and CLI command wiring.

## Scope
- Unit tests for trigger, evidence collectors, check packs, case builders, and memory logic.
- Integration-style tests for `KubeAgentService` orchestration using mocked clients.
- CLI tests for argument parsing and service payload shaping.

## Prerequisites
- Use local Python environment with project dependencies installed.
- `kind` and `kubectl` are required only for functional tests.
- No EKS cluster is required for this suite.

## Run tests
Run fast local tests (unit and integration with mocks) from repository root:
```bash
python -m pytest tests/kube_agent
```

Run one test module:
```bash
python -m pytest tests/kube_agent/test_kube_agent_service_integration.py
```

Start local `kind` cluster first:
```bash
make kind-up
```

Run opt-in functional tests on local `kind`:
```bash
HAPE_RUN_KUBE_AGENT_FUNCTIONAL_TESTS=1 python -m pytest tests/kube_agent/test_kube_agent_functional.py -s
```

## Test behavior notes
- Tests use local mocks for Kubernetes, Prometheus, Alertmanager, and Grafana clients.
- Tests may create temporary SQLite files under pytest temp directories.
- Functional test writes output artifacts under a pytest temp directory:
  - `kube-agent-findings-summary.txt`
  - `kube-agent-findings.json`
  - `kube-agent-findings.md`
  - `kube-agent-findings-slack.txt`
- Functional tests use local `kind` only and do not create or modify cloud infrastructure.

## Cleanup
- Functional tests delete `infrastructure/kubernetes/kube-agent` manifests after completion.
- Functional tests delete the `kind` cluster only if the fixture created it in the same test run.
- Pytest temp files are automatically cleaned up after test runs.
- If local temp artifacts remain after an interrupted run, remove pytest temp directories manually.
