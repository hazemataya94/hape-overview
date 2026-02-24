import os
from typing import List, Optional

from clients.confluence_client import ConfluenceClient
from core.config import Config
from core.errors.exceptions import HapeExternalError, HapeOperationError, HapeValidationError
from core.errors.messages.confluence_error_messages import get_confluence_error_message
from core.logging import LocalLogging
from utils.formatters.confluence_doc_formatter import ConfluenceDocFormatter
from utils.file_manager import FileManager


class ConfluenceService:
    def __init__(self, confluence_client: Optional[ConfluenceClient] = None) -> None:
        self.confluence_client = confluence_client or ConfluenceClient()
        self.logger = LocalLogging.get_logger("hape.confluence_service")
        self.file_manager = FileManager()
        
    def _markdown_to_storage(self, markdown_text: str) -> str:
        return ConfluenceDocFormatter.format_markdown_to_storage(markdown_text)

    def _derive_page_title(self, markdown_text: str, readme_path: str) -> str:
        for line in markdown_text.splitlines():
            if line.startswith("# "):
                title = line.replace("# ", "", 1).strip()
                if title:
                    return title
                break
        fallback = os.path.splitext(os.path.basename(readme_path))[0].strip()
        return fallback or "README"    

    def get_page(self, page_id: str, expand: str = "body.storage") -> dict:
        self.logger.debug(f"get_page(page_id: {page_id}, expand: {expand})")
        if not page_id or not page_id.strip():
            raise HapeValidationError(
                code="CONFLUENCE_PAGE_ID_REQUIRED",
                message=get_confluence_error_message("CONFLUENCE_PAGE_ID_REQUIRED"),
            )
        try:
            return self.confluence_client.get_page(page_id, expand=expand)
        except Exception as exc:
            raise HapeExternalError(
                code="CONFLUENCE_GET_PAGE_FAILED",
                message=get_confluence_error_message(
                    "CONFLUENCE_GET_PAGE_FAILED",
                    page_id=page_id,
                ),
            ) from exc

    def create_page(self, parent_page_id: str, page_title: str, page_body: str, space_key: str, labels: Optional[List[str]] = None) -> dict:
        self.logger.debug(
            "create_page(parent_page_id: {parent_page_id}, page_title: {page_title}, space_key: {space_key})")
        if not parent_page_id or not str(parent_page_id).strip():
            raise HapeValidationError(
                code="CONFLUENCE_PARENT_PAGE_ID_REQUIRED",
                message=get_confluence_error_message("CONFLUENCE_PARENT_PAGE_ID_REQUIRED"),
            )
        if not page_title or not page_title.strip():
            raise HapeValidationError(
                code="CONFLUENCE_PAGE_TITLE_REQUIRED",
                message=get_confluence_error_message("CONFLUENCE_PAGE_TITLE_REQUIRED"),
            )
        if not page_body or not page_body.strip():
            raise HapeValidationError(
                code="CONFLUENCE_PAGE_BODY_REQUIRED",
                message=get_confluence_error_message("CONFLUENCE_PAGE_BODY_REQUIRED"),
            )
        try:
            return self.confluence_client.create_page(
                parent_page_id=parent_page_id,
                page_title=page_title,
                page_body=page_body,
                space_key=space_key,
                labels=labels,
            )
        except Exception as exc:
            raise HapeExternalError(
                code="CONFLUENCE_CREATE_PAGE_FAILED",
                message=get_confluence_error_message(
                    "CONFLUENCE_CREATE_PAGE_FAILED",
                    page_title=page_title,
                ),
            ) from exc

    def get_page_link(self, page_id: str, space_key: str) -> str:
        base_url = self.confluence_client.confluence_base_url
        return f"{base_url}/spaces/{space_key}/pages/{page_id}"

    def create_page_from_markdown(self, readme_path: str, space_key: str, parent_page_id: Optional[str] = None, page_title: Optional[str] = None, labels: Optional[List[str]] = None) -> dict:
        self.logger.debug(f"create_page_from_markdown(parent_page_id: {parent_page_id}, readme_path: {readme_path}, space_key: {space_key})")
        if not readme_path or not readme_path.strip():
            raise HapeValidationError(
                code="CONFLUENCE_README_PATH_REQUIRED",
                message=get_confluence_error_message("CONFLUENCE_README_PATH_REQUIRED"),
            )
        if not self.file_manager.file_exists(readme_path):
            raise HapeValidationError(
                code="CONFLUENCE_README_NOT_FOUND",
                message=get_confluence_error_message(
                    "CONFLUENCE_README_NOT_FOUND",
                    readme_path=readme_path,
                ),
            )
        markdown_text = self.file_manager.read_file(readme_path)
        page_title = page_title or self._derive_page_title(markdown_text, readme_path)
        page_title = "[AUTOGENERATED] " + page_title
        try:
            page_body = self._markdown_to_storage(markdown_text)
        except Exception as exc:
            raise HapeOperationError(
                code="CONFLUENCE_MARKDOWN_CONVERSION_FAILED",
                message=get_confluence_error_message("CONFLUENCE_MARKDOWN_CONVERSION_FAILED"),
            ) from exc
        parent_page_id = parent_page_id or Config.get_test_parent_page_id()
        return self.create_page(
            parent_page_id=parent_page_id,
            page_title=page_title,
            page_body=page_body,
            space_key=space_key,
            labels=labels,
        )
