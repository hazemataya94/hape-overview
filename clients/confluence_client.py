import base64

import requests

from core.config import Config
from core.logging import LocalLogging
from typing import Optional, List
from utils.urls_utils import UrlsUtils


class ConfluenceClient:
    def __init__(self):
        self.logger = LocalLogging.get_logger("hape.confluence_client")
        self.confluence_email = Config.get_atlassian_email()
        self.confluence_api_token = Config.get_atlassian_api_key()
        raw_domain = Config.get_atlassian_domain()
        base_url = UrlsUtils.normalize_atlassian_base_url(raw_domain)
        self.confluence_base_url = self._ensure_wiki_base(base_url)
        self.changelog_parent_page_id = Config.get_changelog_parent_page_id()
        self.changelog_entry_page_template_id = Config.get_changelog_entry_page_template_id()
        self.test_parent_page_id = Config.get_test_parent_page_id()

        if not self.confluence_email:
            raise ValueError("ATLASSIAN_EMAIL is required to access Confluence.")
        if not self.confluence_api_token:
            raise ValueError("ATLASSIAN_API_KEY is required to access Confluence.")

    def _get_auth_headers(self):
        credentials = f"{self.confluence_email}:{self.confluence_api_token}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
        }

    def _ensure_wiki_base(self, base_url):
        normalized = base_url.rstrip("/")
        if normalized.endswith("/wiki"):
            return normalized
        return f"{normalized}/wiki"

    def get_page(self, page_id: str, expand: Optional[str] = None) -> dict:
        self.logger.debug(f"get_page(page_id: {page_id}, expand: {expand})")
        page_url = f"{self.confluence_base_url}/rest/api/content/{page_id}"
        params: dict[str, str] = {}
        if expand:
            params["expand"] = expand
        response = requests.get( page_url, params=params, headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()

    def create_page(self, parent_page_id: str, page_title: str, page_body: str, space_key: str = "FD", labels: Optional[List[str]] = None, set_full_width: bool = True) -> dict:
        self.logger.debug(f"create_page(parent_page_id: {parent_page_id}, page_title: {page_title}, space_key: {space_key})")
        page_url = f"{self.confluence_base_url}/rest/api/content"
        payload = {
            "type": "page",
            "title": page_title,
            "space": {"key": space_key},
            "ancestors": [{"id": str(parent_page_id)}],
            "body": {
                "storage": {
                    "value": page_body,
                    "representation": "storage",
                }
            },
        }
        if labels is not None and isinstance(labels, list):
            label_list = []
            for label in labels:
                label_list.append({"prefix": "global", "name": label})
            payload["metadata"] = {"labels": label_list}
        headers = {
            **self._get_auth_headers(),
            "Content-Type": "application/json",
        }
        response = requests.post(
            page_url,
            headers=headers,
            json=payload,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create Confluence page '{page_title}' (status={response.status_code}): {response.text}")
        new_page = response.json()
        if set_full_width:
            self.set_page_full_width(new_page["id"])
        return new_page

    def set_page_full_width(self, page_id):
        self.logger.debug(f"set_page_full_width(page_id: {page_id})")
        properties_url = f"{self.confluence_base_url}/api/v2/pages/{page_id}/properties"
        headers = {
            **self._get_auth_headers(),
            "Content-Type": "application/json",
        }
        for key in ("content-appearance-draft", "content-appearance-published"):
            response = requests.post(properties_url, headers=headers, json={"key": key, "value": "full-width"})
            response.raise_for_status()
