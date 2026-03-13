from dataclasses import dataclass

from core.config import Config


@dataclass(frozen=True)
class KubeAgentConfig:
    prometheus_base_url: str
    grafana_base_url: str
    grafana_token: str | None
    grafana_username: str | None
    grafana_password: str | None
    alertmanager_base_url: str
    sqlite_path: str
    default_use_ai: bool
    default_slack_channel: str | None
    pod_log_tail_lines: int
    restart_threshold: int
    stale_ai_hours: int
    lookback_minutes: int
    cost_total_hourly_usd_threshold: float
    cost_workload_hourly_usd_threshold: float
    cost_increase_ratio_threshold: float
    cost_top_workloads_limit: int

    @classmethod
    def load(cls) -> "KubeAgentConfig":
        return cls(
            prometheus_base_url=Config.get_kube_agent_prometheus_url(),
            grafana_base_url=Config.get_kube_agent_grafana_url(),
            grafana_token=Config.get_kube_agent_grafana_token() or None,
            grafana_username=Config.get_kube_agent_grafana_username() or None,
            grafana_password=Config.get_kube_agent_grafana_password() or None,
            alertmanager_base_url=Config.get_kube_agent_alertmanager_url(),
            sqlite_path=Config.get_kube_agent_sqlite_path(),
            default_use_ai=Config.get_kube_agent_ai_enabled(),
            default_slack_channel=Config.get_kube_agent_slack_channel() or None,
            pod_log_tail_lines=Config.get_kube_agent_pod_log_tail_lines(),
            restart_threshold=Config.get_kube_agent_restart_threshold(),
            stale_ai_hours=Config.get_kube_agent_ai_stale_hours(),
            lookback_minutes=Config.get_kube_agent_lookback_minutes(),
            cost_total_hourly_usd_threshold=Config.get_kube_agent_cost_total_hourly_usd_threshold(),
            cost_workload_hourly_usd_threshold=Config.get_kube_agent_cost_workload_hourly_usd_threshold(),
            cost_increase_ratio_threshold=Config.get_kube_agent_cost_increase_ratio_threshold(),
            cost_top_workloads_limit=Config.get_kube_agent_cost_top_workloads_limit(),
        )


if __name__ == "__main__":
    print(KubeAgentConfig.load())
