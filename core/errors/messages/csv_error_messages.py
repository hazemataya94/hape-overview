ERROR_MESSAGES = {
    "CSV_JSON_SOURCE_REQUIRED": "Provide one JSON source: --json-file or --json-content.",
    "CSV_JSON_SOURCE_CONFLICT": "Use either --json-file or --json-content, not both.",
    "CSV_OUTPUT_FILE_REQUIRED": "Output file path is required.",
    "CSV_INPUT_FILE_REQUIRED": "CSV input file path is required.",
    "CSV_INPUT_FILE_NOT_FOUND": "CSV file not found: {csv_path}",
    "CSV_JSON_FILE_NOT_FOUND": "JSON file not found: {json_path}",
    "CSV_DELIMITER_INVALID": "CSV delimiter must be exactly one character.",
    "CSV_INVALID_JSON": "Invalid JSON input.",
    "CSV_JSON_ARRAY_REQUIRED": "JSON input must be an array of objects.",
    "CSV_JSON_ARRAY_EMPTY": "JSON input array is empty.",
    "CSV_JSON_ROW_OBJECT_REQUIRED": "Each JSON array item must be an object.",
    "CSV_WRITE_FAILED": "Failed to write CSV output: {output_path}",
    "CSV_READ_FAILED": "Failed to read CSV input: {csv_path}",
    "CSV_WRITE_JSON_FAILED": "Failed to write JSON output: {output_path}",
}


def get_csv_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown CSV error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_csv_error_message("CSV_JSON_SOURCE_REQUIRED"))
