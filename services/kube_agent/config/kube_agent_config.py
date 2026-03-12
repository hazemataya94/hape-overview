import os
from dataclasses import dataclass


@dataclass(frozen=True)
class KubeAgentConfig:
    prometheus_base_url: str
    grafana_base_url: str
    alertmanager_base_url: str
    sqlite_path: str
    default_use_ai: bool
    default_slack_channel: str | None
    pod_log_tail_lines: int
    restart_threshold: int
    stale_ai_hours: int
    lookback_minutes: int

    @staticmethod
    def _read_bool(name: str, default: bool) -> bool:
        raw_value = os.getenv(name, str(default)).strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    @staticmethod
    def _read_int(name: str, default: int) -> int:
        raw_value = os.getenv(name, str(default)).strip()
        try:
            return int(raw_value)
        except ValueError:
            return default

    @classmethod
    def load(cls) -> "KubeAgentConfig":
        return cls(
            prometheus_base_url=os.getenv("HAPE_KUBE_AGENT_PROMETHEUS_URL", "http://localhost:9090").strip(),
            grafana_base_url=os.getenv("HAPE_KUBE_AGENT_GRAFANA_URL", "http://localhost:3000").strip(),
            alertmanager_base_url=os.getenv("HAPE_KUBE_AGENT_ALERTMANAGER_URL", "http://localhost:9093").strip(),
            sqlite_path=os.getenv("HAPE_KUBE_AGENT_SQLITE_PATH", "~/.hape/kube-agent.sqlite").strip(),
            default_use_ai=cls._read_bool("HAPE_KUBE_AGENT_AI_ENABLED", False),
            default_slack_channel=os.getenv("HAPE_KUBE_AGENT_SLACK_CHANNEL", "").strip() or None,
            pod_log_tail_lines=cls._read_int("HAPE_KUBE_AGENT_POD_LOG_TAIL_LINES", 200),
            restart_threshold=cls._read_int("HAPE_KUBE_AGENT_RESTART_THRESHOLD", 3),
            stale_ai_hours=cls._read_int("HAPE_KUBE_AGENT_AI_STALE_HOURS", 6),
            lookback_minutes=cls._read_int("HAPE_KUBE_AGENT_LOOKBACK_MINUTES", 30),
        )


if __name__ == "__main__":
    print(KubeAgentConfig.load())
