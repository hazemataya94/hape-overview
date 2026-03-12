from __future__ import annotations

from typing import Any

import requests

from core.logging import LocalLogging


class AlertmanagerClient:
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(self, base_url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.logger = LocalLogging.get_logger("hape.alertmanager_client")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def list_alerts(self) -> list[dict[str, Any]]:
        self.logger.debug("list_alerts()")
        response = self.session.get(f"{self.base_url}/api/v2/alerts", timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return payload
        return []

    def get_alert(self, alert_fingerprint: str) -> dict[str, Any] | None:
        self.logger.debug(f"get_alert(alert_fingerprint: {alert_fingerprint})")
        if not alert_fingerprint:
            return None
        for alert in self.list_alerts():
            fingerprint = str(alert.get("fingerprint", "")).strip()
            if fingerprint == alert_fingerprint:
                return alert
        return None

    def get_alerts_by_labels(self, matchers: dict[str, str]) -> list[dict[str, Any]]:
        self.logger.debug(f"get_alerts_by_labels(matchers: {matchers})")
        if not matchers:
            return self.list_alerts()
        matched_alerts: list[dict[str, Any]] = []
        for alert in self.list_alerts():
            labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
            if all(str(labels.get(key, "")) == value for key, value in matchers.items()):
                matched_alerts.append(alert)
        return matched_alerts


if __name__ == "__main__":
    alertmanager_client = AlertmanagerClient(base_url="http://localhost:9093")
    print(alertmanager_client.base_url)
