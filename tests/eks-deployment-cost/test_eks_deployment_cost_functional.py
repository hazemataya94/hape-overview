import csv
import json
from pathlib import Path

import pytest

import services.eks_deployment_cost_service as eks_deployment_cost_service_module
from services.eks_deployment_cost_service import EksDeploymentCostService
from utils.test_artifacts_utils import print_artifacts_directory


class _FakeAwsClient:
    _PRICING_BY_INSTANCE_TYPE = {
        "m6i.large": {"hourly_instance_price_usd": 0.12, "vcpu": 2, "memory_gib": 8.0},
        "c6i.large": {"hourly_instance_price_usd": 0.12, "vcpu": 2, "memory_gib": 4.0},
        "r6i.large": {"hourly_instance_price_usd": 0.16, "vcpu": 2, "memory_gib": 16.0},
    }

    def __init__(self, profile_name: str) -> None:
        self.profile_name = profile_name

    def get_region_name(self) -> str:
        return "eu-central-1"

    def get_ec2_instance_type_pricing_details(self, instance_type: str, region_code: str) -> dict:
        pricing = self._PRICING_BY_INSTANCE_TYPE.get(instance_type)
        if not pricing:
            raise ValueError(f"Unexpected instance type in test: {instance_type}")
        return {
            "instance_type": instance_type,
            "region_code": region_code,
            "pricing_location": "EU (Frankfurt)",
            "hourly_instance_price_usd": pricing["hourly_instance_price_usd"],
            "vcpu": pricing["vcpu"],
            "memory_gib": pricing["memory_gib"],
        }


def _read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with open(csv_path, "r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def test_generate_report_on_kind_cluster(apply_test_manifests: dict[str, str | None], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(eks_deployment_cost_service_module, "AwsClient", _FakeAwsClient)
    service = EksDeploymentCostService()
    kube_context = str(apply_test_manifests["kube_context"])
    kubeconfig_path = apply_test_manifests["kubeconfig_path"]
    output_dir = tmp_path / "eks-cost-report"
    outputs = service.generate_report(
        kube_context=kube_context,
        kube_config_file=str(kubeconfig_path) if kubeconfig_path else None,
        aws_profile="dummy-profile",
        aws_region="eu-central-1",
        resource_types_csv="Deployment,StatefulSet",
        namespaces_csv="cost-a,cost-b",
        top_n=20,
        output_dir=str(output_dir),
    )
    summary_json_path = Path(outputs["summary_json_path"])
    details_csv_path = Path(outputs["details_csv_path"])
    assert summary_json_path.exists()
    assert details_csv_path.exists()

    summary = json.loads(summary_json_path.read_text(encoding="utf-8"))
    rows = _read_csv_rows(details_csv_path)

    assert summary["summary"]["workload_count"] == 6
    assert len(rows) == 6
    assert summary["metadata"]["resource_types"] == ["Deployment", "StatefulSet"]
    assert summary["metadata"]["namespaces"] == ["cost-a", "cost-b"]
    assert "m6i.large" in summary["pricing_by_instance_type"]
    assert "c6i.large" in summary["pricing_by_instance_type"]
    assert "r6i.large" in summary["pricing_by_instance_type"]

    top_rows = summary["top_costing_workloads"]
    hourly_values = [float(item["max_hourly_cost_usd"]) for item in top_rows]
    assert hourly_values == sorted(hourly_values, reverse=True)

    rows_by_name = {row["name"]: row for row in rows}

    cpu_only_row = rows_by_name["api-cpu-only"]
    assert int(cpu_only_row["replicas"]) == 3
    assert float(cpu_only_row["cpu_request_cores_per_pod"]) == 0.4
    assert float(cpu_only_row["memory_request_gib_per_pod"]) == 0.0
    assert float(cpu_only_row["hourly_cpu_cost_usd"]) == pytest.approx(0.072, rel=0, abs=1e-6)
    assert float(cpu_only_row["hourly_memory_cost_usd"]) == 0.0
    assert float(cpu_only_row["max_hourly_cost_usd"]) == pytest.approx(0.072, rel=0, abs=1e-6)

    memory_only_row = rows_by_name["api-memory-only"]
    assert int(memory_only_row["replicas"]) == 2
    assert float(memory_only_row["cpu_request_cores_per_pod"]) == 0.0
    assert float(memory_only_row["memory_request_gib_per_pod"]) == 2.0
    assert float(memory_only_row["hourly_cpu_cost_usd"]) == 0.0
    assert float(memory_only_row["hourly_memory_cost_usd"]) == pytest.approx(0.04, rel=0, abs=1e-6)
    assert float(memory_only_row["max_hourly_cost_usd"]) == pytest.approx(0.04, rel=0, abs=1e-6)

    no_request_row = rows_by_name["db-no-requests"]
    assert float(no_request_row["total_cpu_request_cores"]) == 0.0
    assert float(no_request_row["total_memory_request_gib"]) == 0.0
    assert float(no_request_row["hourly_cpu_cost_usd"]) == 0.0
    assert float(no_request_row["hourly_memory_cost_usd"]) == 0.0
    assert float(no_request_row["max_hourly_cost_usd"]) == 0.0

    hourly = float(cpu_only_row["max_hourly_cost_usd"])
    daily = float(cpu_only_row["daily_cost_usd"])
    monthly = float(cpu_only_row["monthly_cost_usd"])
    yearly = float(cpu_only_row["yearly_cost_usd"])
    assert daily == pytest.approx(hourly * 24, rel=0, abs=1e-6)
    assert monthly == pytest.approx(hourly * 24 * 30, rel=0, abs=1e-6)
    assert yearly == pytest.approx(hourly * 24 * 365, rel=0, abs=1e-6)
    print_artifacts_directory(artifacts_directory=output_dir)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
