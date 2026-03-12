from datetime import UTC, datetime

from services.kube_agent.evidence.collectors.pod_metrics_collector import PodMetricsCollector
from services.kube_agent.evidence.evidence_models import EvidenceItem
from services.kube_agent.triggers.trigger_models import Trigger


class PrometheusEvidenceCollector:
    def __init__(self) -> None:
        self.pod_metrics_collector = PodMetricsCollector()

    def _collect_pod_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        return self.pod_metrics_collector.collect(trigger=trigger, prometheus_client=prometheus_client)

    def _collect_node_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        query = f'kube_node_status_condition{{node="{trigger.name}"}}'
        result = prometheus_client.query(promql=query)
        return [EvidenceItem(key="prometheus.node.conditions", source="prometheus", resource_ref=f"node/{trigger.name}", value=result, observed_at=datetime.now(UTC), metadata={"promql": query})]

    def _collect_alert_evidence(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        alert_name = trigger.name
        query = f'ALERTS{{alertname="{alert_name}"}}'
        result = prometheus_client.query(promql=query)
        return [EvidenceItem(key="prometheus.alerts", source="prometheus", resource_ref=f"alert/{alert_name}", value=result, observed_at=datetime.now(UTC), metadata={"promql": query})]

    def collect(self, trigger: Trigger, prometheus_client) -> list[EvidenceItem]:
        if trigger.type == "pod":
            return self._collect_pod_evidence(trigger=trigger, prometheus_client=prometheus_client)
        if trigger.type == "node":
            return self._collect_node_evidence(trigger=trigger, prometheus_client=prometheus_client)
        if trigger.type == "alert":
            return self._collect_alert_evidence(trigger=trigger, prometheus_client=prometheus_client)
        return []


if __name__ == "__main__":
    print(PrometheusEvidenceCollector())
