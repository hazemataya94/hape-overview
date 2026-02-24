ERROR_MESSAGES = {
    "CONFLUENCE_PAGE_ID_REQUIRED": "Confluence page ID is required.",
    "CONFLUENCE_PARENT_PAGE_ID_REQUIRED": "Confluence parent page ID is required.",
    "CONFLUENCE_PAGE_TITLE_REQUIRED": "Confluence page title is required.",
    "CONFLUENCE_PAGE_BODY_REQUIRED": "Confluence page body is required.",
    "CONFLUENCE_README_PATH_REQUIRED": "Confluence markdown path is required.",
    "CONFLUENCE_README_NOT_FOUND": "Markdown file not found: {readme_path}",
    "CONFLUENCE_GET_PAGE_FAILED": "Failed to fetch Confluence page '{page_id}'.",
    "CONFLUENCE_CREATE_PAGE_FAILED": "Failed to create Confluence page '{page_title}'.",
    "CONFLUENCE_MARKDOWN_CONVERSION_FAILED": "Failed to convert markdown to Confluence storage format.",
}


def get_confluence_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown Confluence error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_confluence_error_message("CONFLUENCE_PAGE_ID_REQUIRED"))
