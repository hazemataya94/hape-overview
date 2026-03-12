from __future__ import annotations

from typing import Any

import requests

from core.errors.exceptions import HapeValidationError
from core.logging import LocalLogging


class SlackClient:
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(self, webhook_url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.logger = LocalLogging.get_logger("hape.slack_client")
        self.webhook_url = webhook_url.strip()
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def send_findings(self, message: str, channel: str | None = None) -> None:
        self.logger.debug(f"send_findings(channel: {channel})")
        if not self.webhook_url:
            raise HapeValidationError(code="SLACK_WEBHOOK_REQUIRED", message="Slack webhook URL is required.")
        if not message.strip():
            raise HapeValidationError(code="SLACK_MESSAGE_REQUIRED", message="Slack message is required.")
        payload: dict[str, Any] = {"text": message}
        if channel:
            payload["channel"] = channel
        response = self.session.post(self.webhook_url, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()


if __name__ == "__main__":
    slack_client = SlackClient(webhook_url="https://example.invalid/webhook")
    print(bool(slack_client.webhook_url))
