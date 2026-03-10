import os
import shutil
import subprocess
from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TEST_ROOT.parents[1]
KIND_CONFIG_PATH = REPO_ROOT / "infrastructure" / "kubernetes" / "kind" / "cluster-config.yaml"
TEST_MANIFESTS_DIR = REPO_ROOT / "infrastructure" / "kubernetes" / "eks-deployment-cost" / "manifests"
CLUSTER_NAME = "hape"


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def _is_functional_test_enabled() -> bool:
    return os.getenv("HAPE_RUN_KIND_FUNCTIONAL_TESTS", "0") == "1"


def _ensure_memory_optimized_node_label(kube_context: str) -> None:
    existing_r_node = _run(
        [
            "kubectl",
            "--context",
            kube_context,
            "get",
            "nodes",
            "-l",
            "node.kubernetes.io/instance-type=r6i.large",
            "-o=name",
        ]
    ).stdout.strip()
    if existing_r_node:
        return
    candidate_node = _run(
        [
            "kubectl",
            "--context",
            kube_context,
            "get",
            "nodes",
            "-l",
            "node.kubernetes.io/instance-type=m6i.xlarge",
            "-o=name",
        ]
    ).stdout.strip()
    if not candidate_node:
        return
    candidate_node_name = candidate_node.split("/", 1)[1] if "/" in candidate_node else candidate_node
    _run(
        [
            "kubectl",
            "--context",
            kube_context,
            "label",
            "node",
            candidate_node_name,
            "node.kubernetes.io/instance-type=r6i.large",
            "--overwrite",
        ]
    )


@pytest.fixture(scope="session")
def kind_cluster() -> dict[str, str | None]:
    if not _is_functional_test_enabled():
        pytest.skip("Set HAPE_RUN_KIND_FUNCTIONAL_TESTS=1 to run kind functional tests.")
    if not shutil.which("kind"):
        pytest.skip("kind is required for functional tests.")
    if not shutil.which("kubectl"):
        pytest.skip("kubectl is required for functional tests.")
    list_clusters = _run(["kind", "get", "clusters"])
    cluster_names = [line.strip() for line in list_clusters.stdout.splitlines() if line.strip()]
    cluster_created_in_fixture = False
    if CLUSTER_NAME not in cluster_names:
        _run(["kind", "create", "cluster", "--name", CLUSTER_NAME, "--config", str(KIND_CONFIG_PATH)])
        cluster_created_in_fixture = True
    kube_context = f"kind-{CLUSTER_NAME}"
    kubeconfig_path = os.getenv("KUBECONFIG")
    yield {"kube_context": kube_context, "kubeconfig_path": kubeconfig_path}


@pytest.fixture(scope="session")
def apply_test_manifests(kind_cluster: dict[str, str | None]) -> dict[str, str | None]:
    kube_context = str(kind_cluster["kube_context"])
    _ensure_memory_optimized_node_label(kube_context)
    _run(["kubectl", "--context", kube_context, "apply", "-f", str(TEST_MANIFESTS_DIR / "namespaces.yaml")])
    _run(["kubectl", "--context", kube_context, "apply", "-f", str(TEST_MANIFESTS_DIR / "deployments.yaml")])
    _run(["kubectl", "--context", kube_context, "apply", "-f", str(TEST_MANIFESTS_DIR / "statefulsets.yaml")])
    _run(["kubectl", "--context", kube_context, "-n", "cost-a", "rollout", "status", "deployment/api-with-requests", "--timeout=180s"])
    _run(["kubectl", "--context", kube_context, "-n", "cost-b", "rollout", "status", "deployment/api-no-replicas", "--timeout=180s"])
    _run(["kubectl", "--context", kube_context, "-n", "cost-b", "rollout", "status", "deployment/api-cpu-only", "--timeout=180s"])
    _run(["kubectl", "--context", kube_context, "-n", "cost-b", "rollout", "status", "deployment/api-memory-only", "--timeout=180s"])
    _run(["kubectl", "--context", kube_context, "-n", "cost-a", "rollout", "status", "statefulset/db-with-requests", "--timeout=180s"])
    _run(["kubectl", "--context", kube_context, "-n", "cost-b", "rollout", "status", "statefulset/db-no-requests", "--timeout=180s"])
    return kind_cluster


if __name__ == "__main__":
    print("conftest fixtures for kind functional tests")
