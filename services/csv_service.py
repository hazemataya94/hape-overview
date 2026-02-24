from pathlib import Path

from core.errors.exceptions import HapeOperationError, HapeValidationError
from core.errors.messages.csv_error_messages import get_csv_error_message
from core.logging import LocalLogging
from utils.csv_manager import CsvManager


class CsvService:
    def __init__(self, csv_manager: CsvManager | None = None) -> None:
        self.csv_manager = csv_manager or CsvManager()
        self.logger = LocalLogging.get_logger("hape.csv_service")

    def _read_json_rows_from_file(self, json_file: str) -> list[dict]:
        try:
            return self.csv_manager.read_json_rows(json_file)
        except ValueError as exc:
            self._raise_json_validation_error(exc)
        except Exception as exc:
            raise HapeValidationError(
                code="CSV_INVALID_JSON",
                message=get_csv_error_message("CSV_INVALID_JSON"),
            ) from exc
        raise HapeValidationError(
            code="CSV_INVALID_JSON",
            message=get_csv_error_message("CSV_INVALID_JSON"),
        )

    def _read_json_rows_from_content(self, json_content: str) -> list[dict]:
        try:
            return self.csv_manager.parse_json_rows(json_content)
        except ValueError as exc:
            self._raise_json_validation_error(exc)
        except Exception as exc:
            raise HapeValidationError(
                code="CSV_INVALID_JSON",
                message=get_csv_error_message("CSV_INVALID_JSON"),
            ) from exc
        raise HapeValidationError(
            code="CSV_INVALID_JSON",
            message=get_csv_error_message("CSV_INVALID_JSON"),
        )

    def _raise_json_validation_error(self, error: ValueError) -> None:
        message = str(error)
        if message == "JSON must be an array of objects.":
            raise HapeValidationError(
                code="CSV_JSON_ARRAY_REQUIRED",
                message=get_csv_error_message("CSV_JSON_ARRAY_REQUIRED"),
            ) from error
        if message == "JSON array is empty.":
            raise HapeValidationError(
                code="CSV_JSON_ARRAY_EMPTY",
                message=get_csv_error_message("CSV_JSON_ARRAY_EMPTY"),
            ) from error
        if message == "Each JSON array item must be an object.":
            raise HapeValidationError(
                code="CSV_JSON_ROW_OBJECT_REQUIRED",
                message=get_csv_error_message("CSV_JSON_ROW_OBJECT_REQUIRED"),
            ) from error
        raise HapeValidationError(
            code="CSV_INVALID_JSON",
            message=get_csv_error_message("CSV_INVALID_JSON"),
        ) from error

    def _validate_delimiter(self, delimiter: str) -> None:
        if len(delimiter) != 1:
            raise HapeValidationError(
                code="CSV_DELIMITER_INVALID",
                message=get_csv_error_message("CSV_DELIMITER_INVALID"),
            )

    def from_json(self, output_file: str, json_file: str | None = None, json_content: str | None = None, delimiter: str = ",") -> str:
        self.logger.debug(
            f"from_json(output_file: {output_file}, json_file: {json_file}, json_content_provided: {bool(json_content)}, delimiter: {delimiter})"
        )
        self._validate_delimiter(delimiter)
        if not output_file or not output_file.strip():
            raise HapeValidationError(
                code="CSV_OUTPUT_FILE_REQUIRED",
                message=get_csv_error_message("CSV_OUTPUT_FILE_REQUIRED"),
            )
        if bool(json_file) == bool(json_content):
            code = "CSV_JSON_SOURCE_REQUIRED" if not json_file and not json_content else "CSV_JSON_SOURCE_CONFLICT"
            raise HapeValidationError(
                code=code,
                message=get_csv_error_message(code),
            )
        if json_file:
            if not Path(json_file).exists():
                raise HapeValidationError(
                    code="CSV_JSON_FILE_NOT_FOUND",
                    message=get_csv_error_message("CSV_JSON_FILE_NOT_FOUND", json_path=json_file),
                )
            json_rows = self._read_json_rows_from_file(json_file)
        else:
            json_rows = self._read_json_rows_from_content(json_content or "")
        try:
            self.csv_manager.write_csv(output_file, json_rows, delimiter=delimiter)
        except Exception as exc:
            raise HapeOperationError(
                code="CSV_WRITE_FAILED",
                message=get_csv_error_message("CSV_WRITE_FAILED", output_path=output_file),
            ) from exc
        return output_file

    def to_json(self, csv_file: str, output_file: str, delimiter: str = ",") -> str:
        self.logger.debug(f"to_json(csv_file: {csv_file}, output_file: {output_file}, delimiter: {delimiter})")
        self._validate_delimiter(delimiter)
        if not csv_file or not csv_file.strip():
            raise HapeValidationError(
                code="CSV_INPUT_FILE_REQUIRED",
                message=get_csv_error_message("CSV_INPUT_FILE_REQUIRED"),
            )
        if not output_file or not output_file.strip():
            raise HapeValidationError(
                code="CSV_OUTPUT_FILE_REQUIRED",
                message=get_csv_error_message("CSV_OUTPUT_FILE_REQUIRED"),
            )
        if not Path(csv_file).exists():
            raise HapeValidationError(
                code="CSV_INPUT_FILE_NOT_FOUND",
                message=get_csv_error_message("CSV_INPUT_FILE_NOT_FOUND", csv_path=csv_file),
            )
        try:
            rows = self.csv_manager.read_csv(csv_file, delimiter=delimiter)
        except Exception as exc:
            raise HapeOperationError(
                code="CSV_READ_FAILED",
                message=get_csv_error_message("CSV_READ_FAILED", csv_path=csv_file),
            ) from exc
        try:
            self.csv_manager.write_json(output_file, rows)
        except Exception as exc:
            raise HapeOperationError(
                code="CSV_WRITE_JSON_FAILED",
                message=get_csv_error_message("CSV_WRITE_JSON_FAILED", output_path=output_file),
            ) from exc
        return output_file

def _demo_from_json() -> None:
    csv_service = CsvService()
    output = csv_service.from_json(
        output_file="/tmp/hape_csv_service_from_json.csv",
        json_content='[{"name":"alpha","value":1},{"name":"beta","value":2}]',
    )
    print(output)


def _demo_to_json() -> None:
    csv_service = CsvService()
    output = csv_service.to_json(
        csv_file="/tmp/hape_csv_service_from_json.csv",
        output_file="/tmp/hape_csv_service_to_json.json",
    )
    print(output)


if __name__ == "__main__":
    _demo_from_json()
    _demo_to_json()
