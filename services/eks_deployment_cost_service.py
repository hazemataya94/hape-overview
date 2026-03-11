import csv
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3
import kubernetes.config

from clients.aws_client import AwsClient
from clients.kubernetes_client import KubernetesClient
from core.errors.exceptions import HapeExternalError, HapeOperationError, HapeValidationError
from core.errors.messages.eks_deployment_cost_error_messages import get_eks_deployment_cost_error_message
from core.logging import LocalLogging
from utils.csv_manager import CsvManager
from utils.file_manager import FileManager


class EksDeploymentCostService:
    ALLOWED_RESOURCE_TYPES = ["Deployment", "StatefulSet"]
    HOURS_PER_DAY = 24
    HOURS_PER_MONTH = 24 * 30
    HOURS_PER_YEAR = 24 * 365
    DETAILS_CSV_COLUMNS = [
        "resource_type",
        "namespace",
        "name",
        "instance_type",
        "replicas",
        "cpu_request_cores_per_pod",
        "memory_request_gib_per_pod",
        "total_cpu_request_cores",
        "total_memory_request_gib",
        "usd_per_vcpu_hour",
        "usd_per_gib_hour",
        "hourly_cpu_cost_usd",
        "hourly_memory_cost_usd",
        "max_hourly_cost_usd",
        "daily_cost_usd",
        "monthly_cost_usd",
        "yearly_cost_usd",
    ]

    def __init__(self, csv_manager: CsvManager | None = None, file_manager: FileManager | None = None) -> None:
        self.csv_manager = csv_manager or CsvManager()
        self.file_manager = file_manager or FileManager()
        self.logger = LocalLogging.get_logger("hape.eks_deployment_cost_service")

    @staticmethod
    def _normalize_csv_argument(value: str | None) -> list[str] | None:
        if value is None:
            return None
        raw_items = [item.strip() for item in value.split(",")]
        items = [item for item in raw_items if item]
        return items or None

    def _validate_inputs(self, kube_context: str, output_dir: str, top_n: int, resource_types: list[str], use_incluster_config: bool) -> None:
        if not use_incluster_config and (not kube_context or not kube_context.strip()):
            raise HapeValidationError(code="EDC_KUBE_CONTEXT_REQUIRED", message=get_eks_deployment_cost_error_message("EDC_KUBE_CONTEXT_REQUIRED"))
        if not output_dir or not output_dir.strip():
            raise HapeValidationError(code="EDC_OUTPUT_DIR_REQUIRED", message=get_eks_deployment_cost_error_message("EDC_OUTPUT_DIR_REQUIRED"))
        if top_n <= 0:
            raise HapeValidationError(code="EDC_TOP_N_INVALID", message=get_eks_deployment_cost_error_message("EDC_TOP_N_INVALID"))
        invalid_resource_types = [item for item in resource_types if item not in self.ALLOWED_RESOURCE_TYPES]
        if invalid_resource_types:
            raise HapeValidationError(code="EDC_RESOURCE_TYPES_INVALID", message=get_eks_deployment_cost_error_message("EDC_RESOURCE_TYPES_INVALID", resource_types=", ".join(invalid_resource_types), allowed_resource_types=", ".join(self.ALLOWED_RESOURCE_TYPES)))

    @staticmethod
    def _round_currency(value: float) -> float:
        return round(value, 6)

    def _build_workload_cost_rows(self, workloads: list[dict], pricing_by_instance_type: dict[str, dict]) -> list[dict]:
        rows: list[dict] = []
        for workload in workloads:
            instance_type = workload["instance_type"]
            pricing_details = pricing_by_instance_type[instance_type]
            hourly_instance_price_usd = float(pricing_details["hourly_instance_price_usd"])
            instance_vcpu = float(pricing_details["vcpu"])
            instance_memory_gib = float(pricing_details["memory_gib"])
            usd_per_vcpu_hour = hourly_instance_price_usd / instance_vcpu
            usd_per_gib_hour = hourly_instance_price_usd / instance_memory_gib
            replicas = workload.get("replicas")
            replicas_effective = replicas or 1
            cpu_request_cores_per_pod = float(workload.get("cpu_request_cores_per_pod", 0.0))
            memory_request_gib_per_pod = float(workload.get("memory_request_gib_per_pod", 0.0))
            total_cpu_request_cores = cpu_request_cores_per_pod * replicas_effective
            total_memory_request_gib = memory_request_gib_per_pod * replicas_effective
            hourly_cpu_cost_usd = self._round_currency(total_cpu_request_cores * usd_per_vcpu_hour)
            hourly_memory_cost_usd = self._round_currency(total_memory_request_gib * usd_per_gib_hour)
            max_hourly_cost_usd = self._round_currency(max(hourly_cpu_cost_usd, hourly_memory_cost_usd))
            row = {
                "resource_type": workload.get("resource_type"),
                "namespace": workload.get("namespace"),
                "name": workload.get("name"),
                "instance_type": instance_type,
                "replicas": replicas,
                "cpu_request_cores_per_pod": cpu_request_cores_per_pod,
                "memory_request_gib_per_pod": memory_request_gib_per_pod,
                "total_cpu_request_cores": total_cpu_request_cores,
                "total_memory_request_gib": total_memory_request_gib,
                "usd_per_vcpu_hour": usd_per_vcpu_hour,
                "usd_per_gib_hour": usd_per_gib_hour,
                "hourly_cpu_cost_usd": hourly_cpu_cost_usd,
                "hourly_memory_cost_usd": hourly_memory_cost_usd,
                "max_hourly_cost_usd": max_hourly_cost_usd,
                "daily_cost_usd": self._round_currency(max_hourly_cost_usd * self.HOURS_PER_DAY),
                "monthly_cost_usd": self._round_currency(max_hourly_cost_usd * self.HOURS_PER_MONTH),
                "yearly_cost_usd": self._round_currency(max_hourly_cost_usd * self.HOURS_PER_YEAR),
            }
            rows.append(row)
        return rows

    @staticmethod
    def _sum_cost(rows: list[dict], key: str) -> float:
        return round(sum(float(row.get(key, 0.0)) for row in rows), 6)

    def _build_summary_report(
        self,
        kube_context: str,
        aws_region: str,
        namespaces: list[str] | None,
        ignored_namespaces: list[str],
        resource_types: list[str],
        top_n: int,
        pricing_by_instance_type: dict[str, dict],
        rows_sorted: list[dict],
    ) -> dict:
        top_rows = rows_sorted[:top_n]
        pricing_summary = {}
        for instance_type, pricing_details in pricing_by_instance_type.items():
            pricing_summary[instance_type] = {
                "hourly_instance_price_usd": pricing_details["hourly_instance_price_usd"],
                "vcpu": pricing_details["vcpu"],
                "memory_gib": pricing_details["memory_gib"],
                "usd_per_vcpu_hour": pricing_details["hourly_instance_price_usd"] / pricing_details["vcpu"],
                "usd_per_gib_hour": pricing_details["hourly_instance_price_usd"] / pricing_details["memory_gib"],
            }
        return {
            "metadata": {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "kube_context": kube_context,
                "aws_region": aws_region,
                "namespaces": namespaces if namespaces is not None else ["*"],
                "ignored_namespaces": ignored_namespaces,
                "resource_types": resource_types,
                "top_n": top_n,
            },
            "summary": {
                "workload_count": len(rows_sorted),
                "total_cpu_request_cores": self._sum_cost(rows_sorted, "total_cpu_request_cores"),
                "total_memory_request_gib": self._sum_cost(rows_sorted, "total_memory_request_gib"),
                "hourly_cpu_cost_usd": self._sum_cost(rows_sorted, "hourly_cpu_cost_usd"),
                "hourly_memory_cost_usd": self._sum_cost(rows_sorted, "hourly_memory_cost_usd"),
                "max_hourly_cost_usd": self._sum_cost(rows_sorted, "max_hourly_cost_usd"),
                "daily_cost_usd": self._sum_cost(rows_sorted, "daily_cost_usd"),
                "monthly_cost_usd": self._sum_cost(rows_sorted, "monthly_cost_usd"),
                "yearly_cost_usd": self._sum_cost(rows_sorted, "yearly_cost_usd"),
            },
            "top_costing_workloads": top_rows,
            "pricing_by_instance_type": pricing_summary
        }

    def _write_details_csv(self, output_csv_path: str, rows_sorted: list[dict]) -> None:
        normalized_rows = []
        for row in rows_sorted:
            normalized_row = {}
            for column in self.DETAILS_CSV_COLUMNS:
                normalized_row[column] = row.get(column, "")
            normalized_rows.append(normalized_row)
        if normalized_rows:
            self.csv_manager.write_csv(output_csv_path, normalized_rows)
            return
        with open(output_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.DETAILS_CSV_COLUMNS)
            writer.writeheader()

    @staticmethod
    def _resolve_kube_context(kube_context: str | None, kube_config_file: str | None, use_incluster_config: bool) -> str:
        if use_incluster_config:
            return ""
        if kube_context and kube_context.strip():
            return kube_context.strip()
        try:
            contexts, active_context = kubernetes.config.list_kube_config_contexts(config_file=kube_config_file)
        except Exception as exc:
            raise HapeValidationError(
                code="EDC_KUBE_CONTEXT_REQUIRED",
                message=get_eks_deployment_cost_error_message("EDC_KUBE_CONTEXT_REQUIRED"),
            ) from exc
        if active_context and active_context.get("name"):
            return str(active_context["name"])
        if contexts:
            first_context_name = contexts[0].get("name")
            if first_context_name:
                return str(first_context_name)
        raise HapeValidationError(
            code="EDC_KUBE_CONTEXT_REQUIRED",
            message=get_eks_deployment_cost_error_message("EDC_KUBE_CONTEXT_REQUIRED"),
        )

    @staticmethod
    def _resolve_aws_profile(aws_profile: str | None) -> str | None:
        if aws_profile and aws_profile.strip():
            return aws_profile.strip()
        session = boto3.Session()
        if session.profile_name:
            return session.profile_name
        return None

    @staticmethod
    def _resolve_output_dir(output_dir: str | None) -> str:
        if output_dir and output_dir.strip():
            return output_dir.strip()
        return tempfile.mkdtemp(prefix="hape-eks-deployment-cost-")

    def generate_report(self, kube_context: str | None = None, aws_profile: str | None = None, output_dir: str | None = None, top_n: int = 20, resource_types_csv: str | None = None, namespaces_csv: str | None = None, ignored_namespaces_csv: str | None = None, aws_region: str | None = None, kube_config_file: str | None = None, use_incluster_config: bool = False) -> dict:
        self.logger.debug(
            "generate_report("
            f"kube_context: {kube_context}, aws_profile: {aws_profile}, output_dir: {output_dir}, "
            f"top_n: {top_n}, resource_types_csv: {resource_types_csv}, namespaces_csv: {namespaces_csv}, "
            f"ignored_namespaces_csv: {ignored_namespaces_csv}, aws_region: {aws_region}, kube_config_file: {kube_config_file}, "
            f"use_incluster_config: {use_incluster_config})"
        )
        resolved_kube_context = self._resolve_kube_context(
            kube_context=kube_context,
            kube_config_file=kube_config_file,
            use_incluster_config=use_incluster_config,
        )
        resolved_aws_profile = self._resolve_aws_profile(aws_profile=aws_profile)
        resolved_output_dir = self._resolve_output_dir(output_dir=output_dir)
        resource_types = self._normalize_csv_argument(resource_types_csv) or list(self.ALLOWED_RESOURCE_TYPES)
        namespaces = self._normalize_csv_argument(namespaces_csv)
        ignored_namespaces = self._normalize_csv_argument(ignored_namespaces_csv) or []
        self._validate_inputs(
            kube_context=resolved_kube_context,
            output_dir=resolved_output_dir,
            top_n=top_n,
            resource_types=resource_types,
            use_incluster_config=use_incluster_config,
        )
        kubernetes_client = KubernetesClient(
            context=resolved_kube_context,
            config_file=kube_config_file,
            use_incluster_config=use_incluster_config,
        )
        aws_client = AwsClient(profile_name=resolved_aws_profile)
        effective_region = aws_region or aws_client.get_region_name()
        ignored_namespaces_set = set(ignored_namespaces)
        effective_namespaces = namespaces or kubernetes_client.list_namespaces()
        effective_namespaces = [namespace for namespace in effective_namespaces if namespace not in ignored_namespaces_set]
        try:
            workloads = kubernetes_client.list_replica_workload_request_details(
                resource_types=resource_types,
                namespaces=effective_namespaces,
            )
        except Exception as exc:
            raise HapeExternalError(
                code="EDC_KUBERNETES_READ_FAILED",
                message=get_eks_deployment_cost_error_message("EDC_KUBERNETES_READ_FAILED"),
            ) from exc
        pricing_by_instance_type: dict[str, dict] = {}
        for workload in workloads:
            instance_type = kubernetes_client.get_workload_instance_type_from_pods(
                namespace=workload["namespace"],
                selector_match_labels=workload.get("selector_match_labels", {}),
            )
            if not instance_type:
                raise HapeExternalError(
                    code="EDC_INSTANCE_TYPE_DERIVE_FAILED",
                    message=get_eks_deployment_cost_error_message(
                        "EDC_INSTANCE_TYPE_DERIVE_FAILED",
                        resource_type=workload["resource_type"],
                        namespace=workload["namespace"],
                        name=workload["name"],
                    ),
                )
            workload["instance_type"] = instance_type
            if instance_type in pricing_by_instance_type:
                continue
            try:
                pricing_by_instance_type[instance_type] = aws_client.get_ec2_instance_type_pricing_details(
                    instance_type=instance_type,
                    region_code=effective_region,
                )
            except Exception as exc:
                raise HapeExternalError(
                    code="EDC_AWS_PRICING_LOOKUP_FAILED",
                    message=get_eks_deployment_cost_error_message(
                        "EDC_AWS_PRICING_LOOKUP_FAILED",
                        instance_type=instance_type,
                        region=effective_region,
                    ),
                ) from exc
        rows = self._build_workload_cost_rows(workloads=workloads, pricing_by_instance_type=pricing_by_instance_type)
        rows_sorted = sorted(rows, key=lambda item: item["max_hourly_cost_usd"], reverse=True)
        summary = self._build_summary_report(
            kube_context=resolved_kube_context,
            aws_region=effective_region,
            namespaces=effective_namespaces,
            ignored_namespaces=ignored_namespaces,
            resource_types=resource_types,
            top_n=top_n,
            pricing_by_instance_type=pricing_by_instance_type,
            rows_sorted=rows_sorted,
        )
        output_path = Path(resolved_output_dir)
        summary_json_path = str(output_path / "eks-deployment-cost-summary.json")
        details_csv_path = str(output_path / "eks-deployment-cost-details.csv")
        try:
            self.file_manager.create_directory(resolved_output_dir)
            self.file_manager.write_json_file(summary_json_path, summary)
            self._write_details_csv(details_csv_path, rows_sorted)
        except Exception as exc:
            raise HapeOperationError(
                code="EDC_REPORT_WRITE_FAILED",
                message=get_eks_deployment_cost_error_message("EDC_REPORT_WRITE_FAILED", output_dir=resolved_output_dir),
            ) from exc
        return {
            "summary_json_path": summary_json_path,
            "details_csv_path": details_csv_path,
        }


if __name__ == "__main__":
    eks_deployment_cost_service = EksDeploymentCostService()
    try:
        eks_deployment_cost_service.generate_report(
            kube_context="",
            aws_profile="",
            output_dir="",
        )
    except HapeValidationError as exc:
        print(exc.code)
