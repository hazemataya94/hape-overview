ERROR_MESSAGES = {
    "MARKDOWN_FILE_REQUIRED": "Markdown file path is required.",
    "MARKDOWN_OUTPUT_DIR_REQUIRED": "Output directory path is required.",
    "MARKDOWN_DELIMITER_INVALID": "CSV delimiter must be exactly one character.",
    "MARKDOWN_FILE_NOT_FOUND": "Markdown file not found: {markdown_path}",
    "MARKDOWN_NO_TABLES_FOUND": "No standard pipe tables found in markdown file: {markdown_path}",
    "MARKDOWN_CSV_FILE_REQUIRED": "CSV file path is required.",
    "MARKDOWN_CSV_FILE_NOT_FOUND": "CSV file not found: {csv_path}",
    "MARKDOWN_IMPORT_TARGET_REQUIRED": "Markdown target file path is required.",
    "MARKDOWN_EXPORT_FAILED": "Failed to export markdown tables to CSV files.",
    "MARKDOWN_IMPORT_FAILED": "Failed to import CSV table into markdown file: {markdown_path}",
}


def get_markdown_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown markdown error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_markdown_error_message("MARKDOWN_FILE_REQUIRED"))
