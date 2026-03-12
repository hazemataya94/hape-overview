from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from core.logging import LocalLogging


class PrometheusClient:
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(self, base_url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.logger = LocalLogging.get_logger("hape.prometheus_client")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def query(self, promql: str) -> dict[str, Any]:
        self.logger.debug(f"query(promql: {promql})")
        response = self.session.get(f"{self.base_url}/api/v1/query", params={"query": promql}, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def query_range(self, promql: str, start: datetime, end: datetime, step: str) -> dict[str, Any]:
        self.logger.debug(f"query_range(promql: {promql}, start: {start.isoformat()}, end: {end.isoformat()}, step: {step})")
        response = self.session.get(
            f"{self.base_url}/api/v1/query_range",
            params={"query": promql, "start": start.timestamp(), "end": end.timestamp(), "step": step},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    prometheus_client = PrometheusClient(base_url="http://localhost:9090")
    print(prometheus_client.base_url)
