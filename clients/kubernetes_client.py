import kubernetes.config
import kubernetes.client
import re
import time
from collections import Counter
from typing import Any, Dict, List

from core.logging import LocalLogging
from utils.file_manager import FileManager


class KubernetesClient:
    def __init__(self, context: str | None = None, config_file: str | None = None, use_incluster_config: bool = False) -> None:
        resolved_context = context.strip() if context else ""
        if use_incluster_config:
            kubernetes.config.load_incluster_config()
            resolved_context = "in-cluster"
        elif resolved_context:
            kubernetes.config.load_kube_config(context=resolved_context, config_file=config_file)
        else:
            try:
                kubernetes.config.load_incluster_config()
                resolved_context = "in-cluster"
            except Exception as exc:
                raise ValueError("Error: Kubernetes context is not defined and in-cluster config is unavailable.") from exc

        # Disable TLS verification for this client instance
        configuration = kubernetes.client.Configuration.get_default_copy()
        configuration.verify_ssl = False
        kubernetes.client.Configuration.set_default(configuration)

        self.context = resolved_context
        self.logger = LocalLogging.get_logger("hape.kubernetes_client")
        self.file_manager = FileManager()
        self.core_v1 = kubernetes.client.CoreV1Api()
        self.apps_v1 = kubernetes.client.AppsV1Api()
        self.policy_v1 = kubernetes.client.PolicyV1Api()
        self.autoscaling_v2 = kubernetes.client.AutoscalingV2Api()
        self.apiextensions_v1 = kubernetes.client.ApiextensionsV1Api()
        self.custom_objects = kubernetes.client.CustomObjectsApi()

    def _sanitize_filename(self, name):
        self.logger.debug(f"_sanitize_filename(name: {name})")
        return name.replace("/", "_")

    def _is_node_ready(self, node_name: str) -> bool:
        self.logger.debug(f"_is_node_ready(node_name: {node_name})")
        node = self.core_v1.read_node(node_name)
        conditions = node.status.conditions or []
        for condition in conditions:
            if condition.type == "Ready":
                return condition.status == "True"
        return False

    def _is_pod_ready(self, pod) -> bool:
        self.logger.debug(f"_is_pod_ready(pod: {pod.metadata.name})")
        if pod.status.phase != "Running":
            return False
        conditions = pod.status.conditions or []
        for condition in conditions:
            if condition.type == "Ready":
                return condition.status == "True"
        return False

    def _create_namespaced_pod_eviction(self, namespace: str, pod_name: str, eviction: kubernetes.client.V1Eviction) -> None:
        self.logger.debug(f"_create_namespaced_pod_eviction(namespace: {namespace}, pod_name: {pod_name})")
        if hasattr(self.core_v1, "create_namespaced_pod_eviction"):
            self.core_v1.create_namespaced_pod_eviction(name=pod_name, namespace=namespace, body=eviction)
            return

        if hasattr(self.policy_v1, "create_namespaced_pod_eviction"):
            self.policy_v1.create_namespaced_pod_eviction(name=pod_name, namespace=namespace, body=eviction)
            return

        raise AttributeError("Neither CoreV1Api nor PolicyV1Api exposes create_namespaced_pod_eviction() in installed kubernetes client.")

    @staticmethod
    def _parse_cpu_cores(cpu_text: str | None) -> float:
        if not cpu_text:
            return 0.0
        value = cpu_text.strip()
        if not value:
            return 0.0
        if value.endswith("m"):
            return float(value[:-1]) / 1000.0
        if value.endswith("u"):
            return float(value[:-1]) / 1_000_000.0
        if value.endswith("n"):
            return float(value[:-1]) / 1_000_000_000.0
        return float(value)

    @staticmethod
    def _parse_memory_gib(memory_text: str | None) -> float:
        if not memory_text:
            return 0.0
        value = memory_text.strip()
        if not value:
            return 0.0
        unit_factors = {
            "Ki": 1.0 / (1024.0 ** 2),
            "Mi": 1.0 / 1024.0,
            "Gi": 1.0,
            "Ti": 1024.0,
            "Pi": 1024.0 ** 2,
            "Ei": 1024.0 ** 3,
            "K": 1000.0 / (1024.0 ** 3),
            "M": (1000.0 ** 2) / (1024.0 ** 3),
            "G": (1000.0 ** 3) / (1024.0 ** 3),
            "T": (1000.0 ** 4) / (1024.0 ** 3),
            "P": (1000.0 ** 5) / (1024.0 ** 3),
            "E": (1000.0 ** 6) / (1024.0 ** 3),
        }
        for unit, factor in unit_factors.items():
            if value.endswith(unit):
                return float(value[:-len(unit)]) * factor
        return float(value) / (1024.0 ** 3)

    def _sum_container_requests(self, containers: list) -> tuple[float, float]:
        cpu_total = 0.0
        memory_total = 0.0
        for container in containers or []:
            resources = container.resources
            requests = resources.requests if resources else None
            if not requests:
                continue
            cpu_total += self._parse_cpu_cores(requests.get("cpu"))
            memory_total += self._parse_memory_gib(requests.get("memory"))
        return cpu_total, memory_total

    @staticmethod
    def _build_label_selector(match_labels: dict[str, str]) -> str:
        if not match_labels:
            return ""
        selector_parts = [f"{key}={value}" for key, value in sorted(match_labels.items())]
        return ",".join(selector_parts)

    @staticmethod
    def _get_node_instance_type_label(node) -> str | None:
        labels = node.metadata.labels if node and node.metadata and node.metadata.labels else {}
        return labels.get("node.kubernetes.io/instance-type") or labels.get("beta.kubernetes.io/instance-type")

    def _collect_deployment_request_details(self, namespace: str) -> list[dict[str, Any]]:
        deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
        items: list[dict[str, Any]] = []
        for deployment in deployments.items:
            replicas = deployment.spec.replicas
            containers = deployment.spec.template.spec.containers or []
            cpu_request_cores_per_pod, memory_request_gib_per_pod = self._sum_container_requests(containers=containers)
            items.append(
                {
                    "resource_type": "Deployment",
                    "namespace": namespace,
                    "name": deployment.metadata.name,
                    "replicas": replicas,
                    "selector_match_labels": deployment.spec.selector.match_labels or {},
                    "cpu_request_cores_per_pod": cpu_request_cores_per_pod,
                    "memory_request_gib_per_pod": memory_request_gib_per_pod,
                }
            )
        return items

    def _collect_statefulset_request_details(self, namespace: str) -> list[dict[str, Any]]:
        statefulsets = self.apps_v1.list_namespaced_stateful_set(namespace=namespace)
        items: list[dict[str, Any]] = []
        for statefulset in statefulsets.items:
            replicas = statefulset.spec.replicas
            containers = statefulset.spec.template.spec.containers or []
            cpu_request_cores_per_pod, memory_request_gib_per_pod = self._sum_container_requests(containers=containers)
            items.append(
                {
                    "resource_type": "StatefulSet",
                    "namespace": namespace,
                    "name": statefulset.metadata.name,
                    "replicas": replicas,
                    "selector_match_labels": statefulset.spec.selector.match_labels or {},
                    "cpu_request_cores_per_pod": cpu_request_cores_per_pod,
                    "memory_request_gib_per_pod": memory_request_gib_per_pod,
                }
            )
        return items

    @staticmethod
    def list_contexts():
        LocalLogging.get_logger("hape.kubernetes_client").debug("list_contexts()")
        contexts, _ = kubernetes.config.list_kube_config_contexts()
        return [context["name"] for context in contexts or []]

    def list_namespaces(self) -> list[str]:
        self.logger.debug("list_namespaces()")
        response = self.core_v1.list_namespace()
        return [item.metadata.name for item in response.items if item.metadata and item.metadata.name]

    def list_replica_workload_request_details(self, resource_types: list[str], namespaces: list[str] | None = None) -> list[dict[str, Any]]:
        self.logger.debug(f"list_replica_workload_request_details(resource_types: {resource_types}, namespaces: {namespaces})")
        target_namespaces = namespaces if namespaces else self.list_namespaces()
        items: list[dict[str, Any]] = []
        for namespace in target_namespaces:
            if "Deployment" in resource_types:
                items.extend(self._collect_deployment_request_details(namespace=namespace))
            if "StatefulSet" in resource_types:
                items.extend(self._collect_statefulset_request_details(namespace=namespace))
        return items

    def get_workload_instance_type_from_pods(self, namespace: str, selector_match_labels: dict[str, str]) -> str | None:
        self.logger.debug(
            f"get_workload_instance_type_from_pods(namespace: {namespace}, selector_match_labels: {selector_match_labels})"
        )
        label_selector = self._build_label_selector(match_labels=selector_match_labels)
        if not label_selector:
            return None
        pods = self.core_v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        node_instance_type_counter: Counter[str] = Counter()
        node_cache: dict[str, str | None] = {}
        for pod in pods.items:
            node_name = pod.spec.node_name if pod.spec else None
            if not node_name:
                continue
            if node_name not in node_cache:
                node = self.core_v1.read_node(node_name)
                node_cache[node_name] = self._get_node_instance_type_label(node=node)
            instance_type = node_cache[node_name]
            if instance_type:
                node_instance_type_counter[instance_type] += 1
        if not node_instance_type_counter:
            return None
        return node_instance_type_counter.most_common(1)[0][0]

    def get_statefulset(self, name, namespace):
        self.logger.debug(f"get_statefulset(name: {name}, namespace: {namespace})")
        return self.apps_v1.read_namespaced_stateful_set(name, namespace)

    def get_image_version(self, statefulset, container_keyword):
        self.logger.debug("get_image_version(statefulset: ..., " f"container_keyword: {container_keyword})")
        containers = statefulset.spec.template.spec.containers or []
        container = next((item for item in containers if container_keyword in item.name), None) or (containers[0] if containers else None)
        if not container or not container.image:
            return "unknown"
        image = container.image
        if "@" in image:
            image = image.split("@", 1)[0]
        if ":" in image:
            return image.rsplit(":", 1)[1]
        return "unknown"

    def get_volume_claim_template_name(self, statefulset):
        self.logger.debug("get_volume_claim_template_name(statefulset: ...)")
        templates = statefulset.spec.volume_claim_templates or []
        if not templates:
            raise RuntimeError("No volumeClaimTemplates found on statefulset.")
        for template in templates:
            if template.metadata and template.metadata.name == "prometheus-thanos-db":
                return template.metadata.name
        if len(templates) == 1 and templates[0].metadata:
            return templates[0].metadata.name
        template_names = [template.metadata.name for template in templates if template.metadata and template.metadata.name]
        raise RuntimeError("Multiple volumeClaimTemplates found on statefulset: " f"{template_names}. Unable to determine the Prometheus PVC.")

    def find_pvc_name(self, claim_name, statefulset_name, namespace):
        self.logger.debug("find_pvc_name(" f"claim_name: {claim_name}, statefulset_name: {statefulset_name}, " f"namespace: {namespace})")
        prefix = f"{claim_name}-{statefulset_name}-"
        pvcs = self.core_v1.list_namespaced_persistent_volume_claim(namespace)
        matches = [pvc.metadata.name for pvc in pvcs.items if pvc.metadata.name.startswith(prefix)]
        if not matches:
            raise RuntimeError("No PVCs found for claim template " f"'{claim_name}' with prefix '{prefix}'.")
        if len(matches) > 1:
            raise RuntimeError("Multiple PVCs found for claim template " f"'{claim_name}': {matches}. " "Refine logic or specify a single PVC.")
        return matches[0]

    def get_deployments(self, namespace):
        self.logger.debug(f"get_deployments(namespace: {namespace})")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            return [deployment.metadata.name for deployment in deployments.items]
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing deployments in namespace {namespace}: {e}")
            exit(1)

    def get_deployment_replicas(self, namespace):
        self.logger.debug(f"get_deployment_replicas(namespace: {namespace})")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            return {deployment.metadata.name: deployment.spec.replicas for deployment in deployments.items}
        except kubernetes.client.rest.ApiException as e:
            print(f"Error fetching deployment replicas in namespace {namespace}: {e}")
            exit(1)

    def get_deployment_cost_details(self, namespace):
        self.logger.debug(f"get_deployment_cost_details(namespace: {namespace})")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
        except kubernetes.client.rest.ApiException as e:
            raise RuntimeError(f"Error fetching deployment cost details in namespace {namespace}: {e}")
            
        if not deployments.items:
            return {}
        
        # TODO: fetch cost details from aws pricing api
        per_cpu_cost = 0.0
        per_ram_cost = 0.0
        # per_cpu_cost = aws_client.get_cpu_price(service="EC2", region=region, instance_type=instance_type)
        # per_ram_cost = aws_client.get_price(service="EC2", region=region, instance_type=instance_type)
        
        cost_details = {}
        for deployment in deployments.items:
            name = deployment.metadata.name
            replicas = deployment.spec.replicas or 0
            cpu_limit = "N/A"
            ram_limit = "N/A"

            if deployment.spec.template.spec.containers:
                for container in deployment.spec.template.spec.containers:
                    if container.resources and container.resources.limits:
                        cpu_limit = container.resources.limits.get("cpu", "N/A")
                        ram_limit = container.resources.limits.get("memory", "N/A")
                        break

            # # TODO: Add cost details to the deployment
            # # TODO: fetch cost details from aws pricing api
            # cpu_cost = cpu_request * per_cpu_cost
            # ram_cost = ram_request * per_ram_cost
            # total_cost = cpu_cost + ram_cost
            cost_details[name] = {
                "replicas": replicas,
                # "cpu_request": cpu_request,
                # "ram_request": ram_request,
                "cpu_limit": cpu_limit,
                "ram_limit": ram_limit,
                # "cpu_cost": cpu_cost
                # "ram_cost": ram_cost,
                # "total_cost": total_cost
            }
        return cost_details

        
    def remove_hpa_downscaling_annotations(self, hpa_item):
        self.logger.debug(f"remove_hpa_downscaling_annotations(hpa_item: {hpa_item})")
        if not hpa_item.metadata.annotations:
            return

        annotations = hpa_item.metadata.annotations.copy()
        keys_to_remove = ["downscaler/downtime-replicas", "downscaler/uptime"]

        for key in keys_to_remove:
            annotations.pop(key, None)

        metadata = kubernetes.V1ObjectMeta(annotations=annotations)
        body = kubernetes.V2HorizontalPodAutoscaler(metadata=metadata)

        try:
            self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(name=hpa_item.metadata.name, namespace=hpa_item.metadata.namespace, body=body)
        except kubernetes.client.rest.ApiException as e:
            print("Error removing HPA annotations in " f"{hpa_item.metadata.namespace}/{hpa_item.metadata.name}: {e}")

    def remove_hpa_downscaling_annotations_namespaced(self, namespace):
        self.logger.debug(f"remove_hpa_downscaling_annotations_namespaced(namespace: {namespace})")
        try:
            result = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace)
            for item in result.items:
                self.remove_hpa_downscaling_annotations(item)
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing HPAs in namespace {namespace}: {e}")

    def add_hpa_downscaling_annotations(self, hpa_item):
        self.logger.debug(f"add_hpa_downscaling_annotations(hpa_item: {hpa_item})")
        annotations = hpa_item.metadata.annotations or {}
        annotations["downscaler/downtime-replicas"] = "1"
        annotations["downscaler/uptime"] = "Mon-Fri 05:30-20:30 Europe/Berlin"

        metadata = kubernetes.V1ObjectMeta(annotations=annotations)
        body = kubernetes.V2HorizontalPodAutoscaler(metadata=metadata)

        try:
            self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(name=hpa_item.metadata.name, namespace=hpa_item.metadata.namespace, body=body)
        except kubernetes.client.rest.ApiException as e:
            print("Error adding HPA annotations in " f"{hpa_item.metadata.namespace}/{hpa_item.metadata.name}: {e}")

    def add_hpa_downscaling_annotations_namespaced(self, namespace):
        self.logger.debug(f"add_hpa_downscaling_annotations_namespaced(namespace: {namespace})")
        try:
            result = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace)
            for item in result.items:
                self.add_hpa_downscaling_annotations(item)
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing HPAs in namespace {namespace}: {e}")

    def list_eso_crds(self):
        self.logger.debug("list_eso_crds()")
        try:
            crds = self.apiextensions_v1.list_custom_resource_definition()
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing CRDs: {e}")
            exit(1)
        
        eso_crds = []
        for crd in crds.items:
            group = crd.spec.group
            if not group.endswith("external-secrets.io"):
                continue

            storage_version = None
            for version in crd.spec.versions:
                if version.storage:
                    storage_version = version.name
                    break

            if not storage_version and crd.spec.versions:
                storage_version = crd.spec.versions[0].name

            eso_crds.append({"group": group, "version": storage_version, "kind": crd.spec.names.kind, "plural": crd.spec.names.plural, "scope": crd.spec.scope})

    def list_grafana_custom_resources(self, plural: str) -> list[dict[str, Any]]:
        self.logger.debug(f"list_grafana_custom_resources(plural: {plural})")
        if not plural:
            raise ValueError("Grafana custom resource plural must be defined.")
        return self.get_custom_resources_all_namespaces(group="integreatly.org", version="v1alpha1", plural=plural)

    def get_custom_resources_all_namespaces(self, group, version, plural):
        self.logger.debug("get_custom_resources_all_namespaces(" f"group: {group}, version: {version}, plural: {plural})")
        try:
            result = self.custom_objects.list_cluster_custom_object(group=group, version=version, plural=plural)
            return result.get("items", [])
        except kubernetes.client.rest.ApiException as e:
            print("Error listing custom resources for " f"{group}/{version}/{plural}: {e}")
            exit(1)

    def extract_eso_resources(self, output_dir):
        self.logger.debug(f"extract_eso_resources(output_dir: {output_dir})")
        eso_crds = self.list_eso_crds()

        for crd in eso_crds:
            if not crd["version"]:
                self.logger.warning(f"Skipping CRD with no version: {crd}")
                continue
            resources = self.get_custom_resources_all_namespaces(group=crd["group"], version=crd["version"], plural=crd["plural"])

            kind_dir = crd["kind"].lower()

            for resource in resources:
                metadata = resource.get("metadata", {})
                name = self._sanitize_filename(metadata.get("name", "unknown"))
                namespace = metadata.get("namespace") or "cluster"

                output_path = f"{output_dir}/{kind_dir}/{namespace}"
                self.file_manager.create_directory(output_path)

                file_path = f"{output_path}/{name}.yaml"
                self.file_manager.write_yaml_file(file_path, resource)

    def get_deployment(self, namespace: str, name: str):
        self.logger.debug(f"get_deployment(namespace: {namespace}, name: {name})")
        return self.apps_v1.read_namespaced_deployment(name=name, namespace=namespace)

    def is_deployment_scaled_to_zero(self, namespace: str, name: str) -> bool:
        self.logger.debug(f"is_deployment_scaled_to_zero(namespace: {namespace}, name: {name})")
        deployment = self.get_deployment(namespace=namespace, name=name)
        desired = deployment.spec.replicas or 0
        available = deployment.status.available_replicas or 0
        return desired == 0 and available == 0

    def get_flux_kustomization(self, namespace: str, name: str) -> Dict:
        self.logger.debug(f"get_flux_kustomization(namespace: {namespace}, name: {name})")
        supported_versions = ["v1", "v1beta2", "v1beta1"]
        last_error = None
        for version in supported_versions:
            try:
                return self.custom_objects.get_namespaced_custom_object(group="kustomize.toolkit.fluxcd.io", version=version, namespace=namespace, plural="kustomizations", name=name)
            except kubernetes.client.rest.ApiException as exc:
                if exc.status in (404, 400):
                    last_error = exc
                    continue
                raise
        raise RuntimeError("Could not read Flux Kustomization " f"{namespace}/{name}. Last error: {last_error}")

    def is_flux_kustomization_suspended(self, namespace: str, name: str) -> bool:
        kustomization = self.get_flux_kustomization(namespace=namespace, name=name)
        spec = kustomization.get("spec", {})
        return bool(spec.get("suspend", False))

    def list_node_names_for_node_group(self, node_group_name: str) -> List[str]:
        self.logger.debug(f"list_node_names_for_node_group(node_group_name: {node_group_name})")
        selector = f"eks.amazonaws.com/nodegroup={node_group_name}"
        nodes = self.core_v1.list_node(label_selector=selector)
        names = [item.metadata.name for item in nodes.items if item.metadata]
        names.sort()
        return names

    def wait_for_nodes_ready(self, node_names: List[str], timeout_seconds: int = 1800, poll_seconds: int = 15) -> bool:
        self.logger.debug(
            f"wait_for_nodes_ready(node_names: {node_names}, timeout_seconds: {timeout_seconds}, poll_seconds: {poll_seconds})"
        )
        deadline = time.time() + timeout_seconds
        pending = set(node_names)
        while time.time() < deadline:
            for node_name in list(pending):
                if self._is_node_ready(node_name):
                    pending.remove(node_name)
            if not pending:
                return True
            time.sleep(poll_seconds)
        raise TimeoutError("Timed out waiting for nodes to become Ready: " f"{', '.join(sorted(pending))}")

    def cordon_node(self, node_name: str) -> None:
        self.logger.debug(f"cordon_node(node_name: {node_name})")
        body = {"spec": {"unschedulable": True}}
        self.core_v1.patch_node(node_name, body)

    def uncordon_node(self, node_name: str) -> None:
        self.logger.debug(f"uncordon_node(node_name: {node_name})")
        body = {"spec": {"unschedulable": False}}
        self.core_v1.patch_node(node_name, body)

    def drain_node(self, node_name: str, timeout_seconds: int = 600) -> tuple[bool, List[str]]:
        self.logger.debug(f"drain_node(node_name: {node_name}, timeout_seconds: {timeout_seconds})")
        eviction_errors: List[str] = []
        self.cordon_node(node_name=node_name)
        self.logger.info(f"Cordoned node {node_name}.")

        pods_on_node = self.list_non_daemonset_non_static_pods_on_node(node_name=node_name)
        self.logger.info(f"Found {len(pods_on_node)} non-daemonset/non-static pods on node {node_name}.")

        evicted_pods: List[Dict[str, str]] = []

        for pod in pods_on_node:
            namespace = pod["namespace"]
            pod_name = pod["pod_name"]

            eviction = kubernetes.client.V1Eviction(metadata=kubernetes.client.V1ObjectMeta(name=pod_name, namespace=namespace))
            try:
                self._create_namespaced_pod_eviction(namespace=namespace, pod_name=pod_name, eviction=eviction)
            except kubernetes.client.rest.ApiException as exc:
                error_message = f"ERROR: Eviction failed for {namespace}/{pod_name}: {exc}"
                self.logger.warning(error_message)
                eviction_errors.append(error_message)
                continue

            evicted_pods.append(pod)
            self.logger.info(f"Eviction created for {namespace}/{pod_name}.")
            time.sleep(2)

        deadline = time.time() + timeout_seconds
        pending_pods = evicted_pods
        while pending_pods and time.time() < deadline:
            remaining: List[Dict[str, str]] = []
            for pod in pending_pods:
                current_pod = self.get_pod_if_exists(namespace=pod["namespace"], pod_name=pod["pod_name"])
                if current_pod is None:
                    continue

                if current_pod.metadata.uid != pod["pod_uid"]:
                    continue

                remaining.append(pod)

            pending_pods = remaining
            if pending_pods:
                time.sleep(3)

        if pending_pods:
            pending_names = ", ".join([f"{pod['namespace']}/{pod['pod_name']}" for pod in pending_pods])
            timeout_error = f"ERROR: Timed out waiting for pod deletions after eviction: {pending_names}"
            self.logger.warning(timeout_error)
            return False, [*eviction_errors, timeout_error]

        if eviction_errors:
            self.logger.warning("Drain completed with eviction errors.")
            return False, eviction_errors

        self.logger.info("All successfully evicted pods were deleted.")
        return True, []

    def list_multi_replicas_pods_on_node(self, node_name: str, owner_resource_types: List[str]) -> List[Dict[str, str]]:
        self.logger.debug(
            "list_multi_replicas_pods_on_node(" f"node_name: {node_name}, owner_resource_types: {owner_resource_types})"
        )
        pods = self.core_v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
        multi_replicas_pods: List[Dict[str, str]] = []
        for pod in pods.items:
            owner_refs = pod.metadata.owner_references or []
            owner = next((owner_ref for owner_ref in owner_refs if owner_ref.kind in owner_resource_types), None)
            if not owner:
                continue
            multi_replicas_pods.append(
                {
                    "namespace": pod.metadata.namespace,
                    "owner_kind": owner.kind,
                    "owner_name": owner.name,
                    "pod_name": pod.metadata.name,
                    "pod_uid": pod.metadata.uid,
                }
            )
        return multi_replicas_pods

    def list_non_daemonset_non_static_pods_on_node(self, node_name: str) -> List[Dict[str, str]]:
        self.logger.debug(f"list_non_daemonset_non_static_pods_on_node(node_name: {node_name})")
        pods = self.core_v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
        results: List[Dict[str, str]] = []
        for pod in pods.items:
            owner_refs = pod.metadata.owner_references or []
            if any(owner.kind == "DaemonSet" for owner in owner_refs):
                continue

            annotations = pod.metadata.annotations or {}
            if "kubernetes.io/config.mirror" in annotations:
                continue

            results.append({"namespace": pod.metadata.namespace, "pod_name": pod.metadata.name, "pod_uid": pod.metadata.uid})
        return results

    def get_pod_if_exists(self, namespace: str, pod_name: str):
        self.logger.debug(f"get_pod_if_exists(namespace: {namespace}, pod_name: {pod_name})")
        try:
            return self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        except kubernetes.client.rest.ApiException as exc:
            if exc.status == 404:
                return None
            raise

    def wait_for_pod_relocated_off_node(self, namespace: str, pod_name: str, old_pod_uid: str, old_node_name: str, timeout_seconds: int = 600, poll_seconds: int = 3) -> str:
        self.logger.debug(
            f"wait_for_pod_relocated_off_node(namespace: {namespace}, pod_name: {pod_name}, old_pod_uid: {old_pod_uid}, "
            f"old_node_name: {old_node_name}, timeout_seconds: {timeout_seconds}, poll_seconds: {poll_seconds})"
        )
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            pod = self.get_pod_if_exists(namespace=namespace, pod_name=pod_name)
            if pod is None:
                return "evicted or removed"

            if pod.metadata.uid == old_pod_uid:
                if pod.spec.node_name != old_node_name and self._is_pod_ready(pod):
                    return f"rescheduled to {pod.spec.node_name}"
                time.sleep(poll_seconds)
                continue

            if pod.spec.node_name == old_node_name:
                time.sleep(poll_seconds)
                continue

            if self._is_pod_ready(pod):
                return f"rescheduled to {pod.spec.node_name}"

            time.sleep(poll_seconds)

        raise TimeoutError(
            "Timed out waiting for pod relocation off old node: "
            f"{namespace}/{pod_name} from {old_node_name}"
        )

    def list_multi_replicas_pods(self, namespace: str, owner_resource_name: str, owner_resource_type: str) -> List:
        self.logger.debug(
            "list_multi_replicas_pods("
            f"namespace: {namespace}, owner_resource_name: {owner_resource_name}, owner_resource_type: {owner_resource_type})"
        )
        pods = self.core_v1.list_namespaced_pod(namespace=namespace)
        filtered = []
        for pod in pods.items:
            owner_refs = pod.metadata.owner_references or []
            is_owned = any(owner.kind == owner_resource_type and owner.name == owner_resource_name for owner in owner_refs)
            if is_owned:
                filtered.append(pod)
        return filtered

    def count_multi_replicas_pods_on_node(self, namespace: str, owner_resource_name: str, node_name: str, owner_resource_type: str) -> int:
        self.logger.debug(
            "count_multi_replicas_pods_on_node("
            f"namespace: {namespace}, owner_resource_name: {owner_resource_name}, node_name: {node_name}, "
            f"owner_resource_type: {owner_resource_type})"
        )
        pods = self.list_multi_replicas_pods(namespace, owner_resource_name, owner_resource_type)
        return sum(1 for pod in pods if pod.spec.node_name == node_name)

    def get_multi_replicas_unavailable_pods_count(self, namespace: str, owner_resource_name: str, owner_resource_type: str) -> int:
        self.logger.debug(
            "get_multi_replicas_unavailable_pods_count("
            f"namespace: {namespace}, owner_resource_name: {owner_resource_name}, owner_resource_type: {owner_resource_type})"
        )
        if owner_resource_type == "StatefulSet":
            resource = self.apps_v1.read_namespaced_stateful_set(owner_resource_name, namespace)
            desired = resource.spec.replicas or 0
        elif owner_resource_type == "ReplicaSet":
            resource = self.apps_v1.read_namespaced_replica_set(owner_resource_name, namespace)
            desired = resource.spec.replicas or 0
        elif owner_resource_type == "StrimziPodSet":
            resource = self.custom_objects.get_namespaced_custom_object(
                group="core.strimzi.io",
                version="v1beta2",
                namespace=namespace,
                plural="strimzipodsets",
                name=owner_resource_name,
            )
            desired = int(resource.get("spec", {}).get("replicas") or 0)
        else:
            raise ValueError(f"Unsupported owner resource type: {owner_resource_type}")
        pods = self.list_multi_replicas_pods(namespace=namespace, owner_resource_name=owner_resource_name, owner_resource_type=owner_resource_type)
        ready = sum(1 for pod in pods if self._is_pod_ready(pod))
        unavailable = desired - ready
        if unavailable < 0:
            return 0
        return unavailable

    def delete_pod(self, namespace: str, pod_name: str) -> None:
        self.logger.debug(f"delete_pod(namespace: {namespace}, pod_name: {pod_name})")
        self.core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)

    def get_pod(self, namespace: str, pod_name: str):
        self.logger.debug(f"get_pod(namespace: {namespace}, pod_name: {pod_name})")
        return self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    def wait_for_recreated_pod_ready(self, namespace: str, pod_name: str, old_pod_uid: str, timeout_seconds: int = 1800, poll_seconds: int = 10) -> None:
        self.logger.debug(
            f"wait_for_recreated_pod_ready(namespace: {namespace}, pod_name: {pod_name}, old_pod_uid: {old_pod_uid}, "
            f"timeout_seconds: {timeout_seconds}, poll_seconds: {poll_seconds})"
        )
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            if pod.metadata.uid == old_pod_uid:
                time.sleep(poll_seconds)
                continue
            if self._is_pod_ready(pod):
                return
            time.sleep(poll_seconds)
        raise TimeoutError(f"Timed out waiting for recreated pod readiness: {namespace}/{pod_name}")

    def read_pod_logs(self, namespace: str, pod_name: str, since_seconds: int = 600, tail_lines: int = 1000) -> str:
        self.logger.debug(
            f"read_pod_logs(namespace: {namespace}, pod_name: {pod_name}, since_seconds: {since_seconds}, tail_lines: {tail_lines})"
        )
        return self.core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, since_seconds=since_seconds, tail_lines=tail_lines)

    def pod_logs_have_errors(self, namespace: str, pod_name: str, error_regex: str, allowlist_regexes: List[str], since_seconds: int = 600) -> bool:
        self.logger.debug(
            f"pod_logs_have_errors(namespace: {namespace}, pod_name: {pod_name}, error_regex: {error_regex}, "
            f"allowlist_regexes: {allowlist_regexes}, since_seconds: {since_seconds})"
        )
        logs = self.read_pod_logs(namespace=namespace, pod_name=pod_name, since_seconds=since_seconds)
        if not logs:
            return False
        error_pattern = re.compile(error_regex)
        allowlist_patterns = [re.compile(pattern) for pattern in allowlist_regexes]
        for line in logs.splitlines():
            if not error_pattern.search(line):
                continue
            is_allowlisted = any(pattern.search(line) for pattern in allowlist_patterns)
            if not is_allowlisted:
                return True
        return False

    def list_pdbs_with_zero_disruptions_allowed(self) -> List[Dict[str, str]]:
        self.logger.debug("list_pdbs_with_zero_disruptions_allowed()")
        pdbs = self.policy_v1.list_pod_disruption_budget_for_all_namespaces()
        blocked: List[Dict[str, str]] = []
        for pdb in pdbs.items:
            disruptions_allowed = pdb.status.disruptions_allowed or 0
            if disruptions_allowed == 0:
                blocked.append({"namespace": pdb.metadata.namespace, "name": pdb.metadata.name})
        return blocked


if __name__ == "__main__":
    
    kubernetes_client = KubernetesClient(context="infrastructure")

    deployment_name = "kubernetes-client-test"
    namespace = "my_namespace"
    flux_kustomization_name = "my_flux_kustomization"
    flux_kustomization_namespace = "my_namespace"

    statefulset_name = "kubernetes-client-test"
    statefulset_namespace = "my_namespace"

    node_name = "ip-x-x-x-x.eu-central-1.compute.internal"
    print("Hello, world!")

    namespace = "ingress"
    pod_name="ingress-nginx-controller-x-x-x-x"
    # kubernetes_client.drain_node(namespace="ingress", pod_name="ingress-nginx-controller-x-x-x-x")
    eviction = kubernetes.client.V1Eviction(metadata=kubernetes.client.V1ObjectMeta(name=pod_name, namespace=namespace))
    kubernetes_client._create_namespaced_pod_eviction(namespace=namespace, pod_name=pod_name, eviction=eviction)

    # print("Getting deployment")
    # deployment = kubernetes_client.get_deployment(namespace=namespace, name=deployment_name)
    # print(deployment)
    # input("Press Enter to continue...")

    # print("Checking if deployment is scaled to zero")
    # is_deployment_scaled_to_zero = kubernetes_client.is_deployment_scaled_to_zero(namespace=namespace, name=deployment_name)
    # print(is_deployment_scaled_to_zero)
    # input("Press Enter to continue...")
    
    # print("Getting flux kustomization")
    # flux_kustomization = kubernetes_client.get_flux_kustomization(namespace=flux_kustomization_namespace, name=flux_kustomization_name)
    # print(flux_kustomization)
    # input("Press Enter to continue...")
    
    # print("Checking if flux kustomization is suspended")
    # is_flux_kustomization_suspended = kubernetes_client.is_flux_kustomization_suspended(namespace=namespace, name=flux_kustomization_name)
    # print(is_flux_kustomization_suspended)
    # input("Press Enter to continue...")
