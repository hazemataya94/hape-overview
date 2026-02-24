import os
import shutil
import subprocess
import tempfile

from clients.jira_client import JiraClient
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.jira_error_messages import get_jira_error_message
from core.logging import LocalLogging
from utils.formatters.jira_comment_formatter import JiraCommentFormatter
from utils.file_manager import FileManager


class JiraService:
    _DEFAULT_MERMAID_WIDTH = 1200

    def __init__(self, jira_client: JiraClient | None = None) -> None:
        self.jira_client = jira_client or JiraClient()
        self.file_manager = FileManager()
        self.logger = LocalLogging.get_logger("hape.jira_service")

    def _attach_mermaid_images(self, issue_key: str, comment_body: str, mermaid_blocks: list[str]) -> str:
        self.logger.debug(f"_attach_mermaid_images(issue_key: {issue_key}, mermaid_block_count: {len(mermaid_blocks)})")
        for index, mermaid_code in enumerate(mermaid_blocks):
            filename = f"mermaid-diagram-{index + 1}.png"
            self.logger.debug(f"Rendering mermaid block index={index} to attachment filename={filename}")
            try:
                image_bytes = self._render_mermaid_png(mermaid_code)
            except Exception as exc:
                raise HapeExternalError(code="JIRA_MERMAID_RENDER_FAILED", message=get_jira_error_message("JIRA_MERMAID_RENDER_FAILED")) from exc

            try:
                width, height = self._get_png_dimensions(image_bytes)
                size_params = self._format_image_size(width, height)
            except ValueError as exc:
                self.logger.warning(f"Unable to read PNG dimensions ({exc}); falling back to width={self._DEFAULT_MERMAID_WIDTH}.")
                size_params = f"|width={self._DEFAULT_MERMAID_WIDTH}"

            try:
                attachments = self.jira_client.add_attachment(issue_key=issue_key, filename=filename, content_bytes=image_bytes, content_type="image/png")
            except Exception as exc:
                raise HapeExternalError(code="JIRA_ADD_ATTACHMENT_FAILED", message=get_jira_error_message("JIRA_ADD_ATTACHMENT_FAILED", issue_key=issue_key)) from exc

            if not attachments:
                raise HapeExternalError(code="JIRA_ADD_ATTACHMENT_FAILED", message=get_jira_error_message("JIRA_ADD_ATTACHMENT_FAILED", issue_key=issue_key))

            first_attachment = attachments[0]
            actual_filename = first_attachment.get("filename", filename)
            if not isinstance(actual_filename, str) or not actual_filename.strip():
                actual_filename = filename

            placeholder = f"@@JIRA_MERMAID_{index}@@"
            comment_body = comment_body.replace(placeholder, f"!{actual_filename}{size_params}!")
            self.logger.debug(f"Attached mermaid image filename={actual_filename} for issue_key={issue_key}")
        return comment_body

    def _render_mermaid_png(self, mermaid_code: str) -> bytes:
        self.logger.debug(f"_render_mermaid_png(mermaid_code_length: {len(mermaid_code)})")
        with tempfile.TemporaryDirectory(prefix="hape-mermaid-") as tmp_dir:
            input_path = os.path.join(tmp_dir, "diagram.mmd")
            output_path = os.path.join(tmp_dir, "diagram.png")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code.strip() + "\n")

            width = str(self._DEFAULT_MERMAID_WIDTH)

            if shutil.which("mmdc"):
                cmd = ["mmdc", "-i", input_path, "-o", output_path, "-w", width, "-b", "transparent"]
                self._run_renderer(cmd, "mmdc")

            elif shutil.which("docker"):
                image = "ghcr.io/mermaid-js/mermaid-cli/mermaid-cli"
                volume = f"{tmp_dir}:/data"

                cmd = ["docker", "run", "--rm", "-v", volume]

                # Keep output files owned by the current user on Linux.
                # On macOS Docker Desktop, this is usually not needed, but it is harmless.
                if hasattr(os, "getuid") and hasattr(os, "getgid"):
                    cmd.extend(["-u", f"{os.getuid()}:{os.getgid()}"])

                cmd.extend([image, "-i", "/data/diagram.mmd", "-o", "/data/diagram.png", "-w", width, "-b", "transparent"])

                self._run_renderer(cmd, "docker")

            else:
                raise RuntimeError("No Mermaid renderer found. Install `mmdc` (npm @mermaid-js/mermaid-cli) or Docker.")

            if not os.path.exists(output_path):
                raise RuntimeError("Mermaid renderer did not produce an output image.")

            with open(output_path, "rb") as f:
                return f.read()

    def _run_renderer(self, command: list[str], backend: str) -> None:
        self.logger.debug(f"Rendering Mermaid diagram locally via {backend}: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            details = "\n".join([x for x in [stdout, stderr] if x]).strip()
            raise RuntimeError(f"Mermaid renderer failed (backend={backend}).\n{details}")

    def _get_png_dimensions(self, image_bytes: bytes) -> tuple[int, int]:
        self.logger.debug(f"_get_png_dimensions(image_bytes_length: {len(image_bytes)})")
        if image_bytes[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Unexpected image format; expected PNG.")
        if image_bytes[12:16] != b"IHDR":
            raise ValueError("Invalid PNG header.")
        width = int.from_bytes(image_bytes[16:20], "big")
        height = int.from_bytes(image_bytes[20:24], "big")
        return width, height

    def _format_image_size(self, width: int, height: int) -> str:
        self.logger.debug(f"_format_image_size(width: {width}, height: {height})")
        if width == 0 or height == 0:
            return f"|width={self._DEFAULT_MERMAID_WIDTH}"
        if width >= height:
            return f"|width={self._DEFAULT_MERMAID_WIDTH}"
        return "|height=600"

    def get_issue(self, issue_key: str) -> dict:
        self.logger.debug(f"get_issue(issue_key: {issue_key})")
        if not issue_key or not issue_key.strip():
            raise HapeValidationError(code="JIRA_ISSUE_KEY_REQUIRED", message=get_jira_error_message("JIRA_ISSUE_KEY_REQUIRED"))
        try:
            issue = self.jira_client.get_issue(issue_key)
            self.logger.debug(f"get_issue completed(issue_key: {issue_key})")
            return issue
        except Exception as exc:
            raise HapeExternalError(code="JIRA_GET_ISSUE_FAILED", message=get_jira_error_message("JIRA_GET_ISSUE_FAILED", issue_key=issue_key)) from exc

    def get_issue_remote_links(self, issue_key: str) -> list[dict]:
        self.logger.debug(f"get_issue_remote_links(issue_key: {issue_key})")
        if not issue_key or not issue_key.strip():
            raise HapeValidationError(code="JIRA_ISSUE_KEY_REQUIRED", message=get_jira_error_message("JIRA_ISSUE_KEY_REQUIRED"))
        try:
            remote_links = self.jira_client.get_issue_remote_links(issue_key)
            self.logger.debug(f"get_issue_remote_links completed(issue_key: {issue_key}, link_count: {len(remote_links)})")
            return remote_links
        except Exception as exc:
            raise HapeExternalError(code="JIRA_GET_REMOTE_LINKS_FAILED", message=get_jira_error_message("JIRA_GET_REMOTE_LINKS_FAILED", issue_key=issue_key)) from exc

    def get_issue_url(self, issue_key: str) -> str:
        self.logger.debug(f"get_issue_url(issue_key: {issue_key})")
        if not issue_key or not issue_key.strip():
            raise HapeValidationError(code="JIRA_ISSUE_KEY_REQUIRED", message=get_jira_error_message("JIRA_ISSUE_KEY_REQUIRED"))
        try:
            issue_url = self.jira_client.get_issue_url(issue_key)
            self.logger.debug(f"get_issue_url completed(issue_key: {issue_key})")
            return issue_url
        except Exception as exc:
            raise HapeExternalError(code="JIRA_GET_ISSUE_URL_FAILED", message=f"Failed to build Jira issue URL for '{issue_key}'.") from exc

    def add_comment_from_markdown(self, issue_key: str, markdown_path: str) -> dict:
        self.logger.debug(f"add_comment_from_markdown(issue_key: {issue_key}, markdown_path: {markdown_path})")
        if not issue_key or not issue_key.strip():
            raise HapeValidationError(code="JIRA_ISSUE_KEY_REQUIRED", message=get_jira_error_message("JIRA_ISSUE_KEY_REQUIRED"))
        if not markdown_path or not markdown_path.strip():
            raise HapeValidationError(code="JIRA_MARKDOWN_PATH_REQUIRED", message=get_jira_error_message("JIRA_MARKDOWN_PATH_REQUIRED"))
        if not self.file_manager.file_exists(markdown_path):
            raise HapeValidationError(code="JIRA_MARKDOWN_NOT_FOUND", message=get_jira_error_message("JIRA_MARKDOWN_NOT_FOUND", markdown_path=markdown_path))
        markdown_text = self.file_manager.read_file(markdown_path)
        self.logger.debug(f"Loaded markdown for jira comment(issue_key: {issue_key}, markdown_length: {len(markdown_text)})")
        comment_body, mermaid_blocks = JiraCommentFormatter.format_markdown_to_jira_wiki_with_mermaid(markdown_text)
        self.logger.debug(f"Converted markdown to jira body(issue_key: {issue_key}, mermaid_block_count: {len(mermaid_blocks)})")
        if mermaid_blocks:
            comment_body = self._attach_mermaid_images(issue_key=issue_key, comment_body=comment_body, mermaid_blocks=mermaid_blocks)
        try:
            response = self.jira_client.add_comment(issue_key, comment_body)
            self.logger.debug(f"add_comment_from_markdown completed(issue_key: {issue_key})")
            return response
        except Exception as exc:
            raise HapeExternalError(code="JIRA_ADD_COMMENT_FAILED", message=get_jira_error_message("JIRA_ADD_COMMENT_FAILED", issue_key=issue_key)) from exc
