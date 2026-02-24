"""Domain error message catalogs."""

from core.errors.messages.config_error_messages import get_config_error_message
from core.errors.messages.confluence_error_messages import get_confluence_error_message
from core.errors.messages.gitlab_error_messages import get_gitlab_error_message
from core.errors.messages.jira_error_messages import get_jira_error_message
from core.errors.messages.kubernetes_error_messages import get_kubernetes_error_message
from core.errors.messages.csv_error_messages import get_csv_error_message
from core.errors.messages.markdown_error_messages import get_markdown_error_message

__all__ = [
    "get_config_error_message",
    "get_confluence_error_message",
    "get_gitlab_error_message",
    "get_jira_error_message",
    "get_kubernetes_error_message",
    "get_csv_error_message",
    "get_markdown_error_message",
]


if __name__ == "__main__":
    print(get_config_error_message("CONFIG_ENV_INT_REQUIRED"))
