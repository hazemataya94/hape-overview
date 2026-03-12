import os
import shutil
import subprocess
from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TEST_ROOT.parents[1]
KIND_CONFIG_PATH = REPO_ROOT / "infrastructure" / "kubernetes" / "kind" / "cluster-config.yaml"
TEST_KUSTOMIZE_DIR = REPO_ROOT / "infrastructure" / "kubernetes" / "kube-agent"
CLUSTER_NAME = "hape"
TEST_NAMESPACE = "kube-agent-test"
TEST_DEPLOYMENT_NAME = "kube-agent-api"


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def _is_functional_test_enabled() -> bool:
    return os.getenv("HAPE_RUN_KUBE_AGENT_FUNCTIONAL_TESTS", "0") == "1"


@pytest.fixture(scope="session")
def functional_kind_cluster() -> dict[str, str | None]:
    if not _is_functional_test_enabled():
        pytest.skip("Set HAPE_RUN_KUBE_AGENT_FUNCTIONAL_TESTS=1 to run kube-agent functional tests.")
    if not shutil.which("kind"):
        pytest.skip("kind is required for kube-agent functional tests.")
    if not shutil.which("kubectl"):
        pytest.skip("kubectl is required for kube-agent functional tests.")
    list_clusters = _run(["kind", "get", "clusters"])
    cluster_names = [line.strip() for line in list_clusters.stdout.splitlines() if line.strip()]
    cluster_created_in_fixture = False
    if CLUSTER_NAME not in cluster_names:
        _run(["kind", "create", "cluster", "--name", CLUSTER_NAME, "--config", str(KIND_CONFIG_PATH)])
        cluster_created_in_fixture = True
    kube_context = f"kind-{CLUSTER_NAME}"
    kubeconfig_path = os.getenv("KUBECONFIG")
    yield {"kube_context": kube_context, "kubeconfig_path": kubeconfig_path}
    _run(["kubectl", "--context", kube_context, "delete", "-k", str(TEST_KUSTOMIZE_DIR)])
    if cluster_created_in_fixture:
        _run(["kind", "delete", "cluster", "--name", CLUSTER_NAME])


@pytest.fixture(scope="session")
def apply_kube_agent_test_manifests(functional_kind_cluster: dict[str, str | None]) -> dict[str, str | None]:
    kube_context = str(functional_kind_cluster["kube_context"])
    _run(["kubectl", "--context", kube_context, "apply", "-k", str(TEST_KUSTOMIZE_DIR)])
    _run(
        [
            "kubectl",
            "--context",
            kube_context,
            "-n",
            TEST_NAMESPACE,
            "rollout",
            "status",
            f"deployment/{TEST_DEPLOYMENT_NAME}",
            "--timeout=180s",
        ]
    )
    pod_name = _run(
        [
            "kubectl",
            "--context",
            kube_context,
            "-n",
            TEST_NAMESPACE,
            "get",
            "pods",
            "-l",
            "app=kube-agent-api",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
    ).stdout.strip()
    return {
        "kube_context": kube_context,
        "kubeconfig_path": functional_kind_cluster["kubeconfig_path"],
        "namespace": TEST_NAMESPACE,
        "deployment": TEST_DEPLOYMENT_NAME,
        "pod": pod_name,
    }


if __name__ == "__main__":
    print("kube-agent functional test fixtures")
