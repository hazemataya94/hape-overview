import base64

import requests

from core.config import Config
from core.logging import LocalLogging
from utils.urls_utils import UrlsUtils


class JiraClient:
    def __init__(self):
        self.logger = LocalLogging.get_logger("hape.jira_client")
        self.jira_email = Config.get_atlassian_email()
        self.jira_api_token = Config.get_atlassian_api_key()
        raw_domain = Config.get_atlassian_domain()
        self.jira_base_url = UrlsUtils.normalize_atlassian_base_url(raw_domain)

        if not self.jira_email:
            raise ValueError("ATLASSIAN_EMAIL is required to access Jira.")
        if not self.jira_api_token:
            raise ValueError("ATLASSIAN_API_KEY is required to access Jira.")

    def _get_auth_headers(self):
        credentials = f"{self.jira_email}:{self.jira_api_token}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
        }

    def get_issue(self, issue_key):
        self.logger.debug(f"get_issue(issue_key: {issue_key})")
        issue_url = f"{self.jira_base_url}/rest/api/3/issue/{issue_key}"
        response = requests.get(issue_url, headers=self._get_auth_headers())
        if response.status_code != 200:
            raise RuntimeError(
                "Failed to fetch Jira issue "
                f"'{issue_key}' (status={response.status_code}): {response.text}"
            )
        return response.json()

    def get_issue_remote_links(self, issue_key):
        self.logger.debug(f"get_issue_remote_links(issue_key: {issue_key})")
        links_url = f"{self.jira_base_url}/rest/api/3/issue/{issue_key}/remotelink"
        response = requests.get(links_url, headers=self._get_auth_headers())
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch Jira issue remote links '{issue_key}' (status={response.status_code}): {response.text}")
        return response.json()

    def add_comment(self, issue_key: str, comment_body: str) -> dict:
        self.logger.debug(f"add_comment(issue_key: {issue_key})")
        comment_url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}/comment"
        headers = {
            **self._get_auth_headers(),
            "Content-Type": "application/json",
        }
        response = requests.post(
            comment_url,
            headers=headers,
            json={"body": comment_body},
        )
        response.raise_for_status()
        return response.json()

    def add_attachment(self, issue_key: str, filename: str, content_bytes: bytes, content_type: str = "application/octet-stream") -> list:
        self.logger.debug(f"add_attachment(issue_key: {issue_key}, filename: {filename})")
        attachment_url = f"{self.jira_base_url}/rest/api/2/issue/{issue_key}/attachments"
        headers = {
            **self._get_auth_headers(),
            "X-Atlassian-Token": "no-check",
        }
        files = {
            "file": (filename, content_bytes, content_type),
        }
        response = requests.post(attachment_url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()

    def get_issue_url(self, issue_key: str) -> str:
        return f"{self.jira_base_url}/browse/{issue_key}"
