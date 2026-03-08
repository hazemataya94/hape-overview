ERROR_MESSAGES = {
    "JIRA_ISSUE_KEY_REQUIRED": "Jira issue key is required.",
    "JIRA_MARKDOWN_PATH_REQUIRED": "Markdown path is required.",
    "JIRA_MARKDOWN_NOT_FOUND": "Markdown file not found: {markdown_path}",
    "JIRA_GET_ISSUE_FAILED": "Failed to fetch Jira issue '{issue_key}'.",
    "JIRA_GET_REMOTE_LINKS_FAILED": "Failed to fetch Jira remote links for '{issue_key}'.",
    "JIRA_ADD_COMMENT_FAILED": "Failed to add Jira comment for '{issue_key}'.",
    "JIRA_ADD_ATTACHMENT_FAILED": "Failed to add Jira attachment for '{issue_key}'.",
    "JIRA_MERMAID_RENDER_FAILED": "Failed to render Mermaid diagram for Jira comment. Install `mmdc` (npm @mermaid-js/mermaid-cli) or Docker.",
    "JIRA_COMMENT_BODY_TOO_LONG": "Jira comment body exceeds maximum allowed length ({max_length} characters). Current length: {current_length} characters.",
}


def get_jira_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown Jira error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_jira_error_message("JIRA_ISSUE_KEY_REQUIRED"))
