from pathlib import Path

from core.errors.exceptions import HapeOperationError, HapeValidationError
from core.errors.messages.markdown_error_messages import get_markdown_error_message
from core.logging import LocalLogging
from utils.csv_manager import CsvManager
from utils.markdown_manager import MarkdownManager


class MarkdownService:
    def __init__(self, markdown_manager: MarkdownManager | None = None, csv_manager: CsvManager | None = None) -> None:
        self.markdown_manager = markdown_manager or MarkdownManager()
        self.csv_manager = csv_manager or CsvManager()
        self.logger = LocalLogging.get_logger("hape.markdown_service")

    def _validate_delimiter(self, delimiter: str) -> None:
        if len(delimiter) != 1:
            raise HapeValidationError(
                code="MARKDOWN_DELIMITER_INVALID",
                message=get_markdown_error_message("MARKDOWN_DELIMITER_INVALID"),
            )

    def export_tables_to_csv(self, markdown_file: str, output_dir: str, delimiter: str = ",") -> list[str]:
        self.logger.debug(
            f"export_tables_to_csv(markdown_file: {markdown_file}, output_dir: {output_dir}, delimiter: {delimiter})"
        )
        self._validate_delimiter(delimiter)
        if not markdown_file or not markdown_file.strip():
            raise HapeValidationError(
                code="MARKDOWN_FILE_REQUIRED",
                message=get_markdown_error_message("MARKDOWN_FILE_REQUIRED"),
            )
        if not output_dir or not output_dir.strip():
            raise HapeValidationError(
                code="MARKDOWN_OUTPUT_DIR_REQUIRED",
                message=get_markdown_error_message("MARKDOWN_OUTPUT_DIR_REQUIRED"),
            )

        markdown_path = Path(markdown_file)
        if not markdown_path.exists():
            raise HapeValidationError(
                code="MARKDOWN_FILE_NOT_FOUND",
                message=get_markdown_error_message("MARKDOWN_FILE_NOT_FOUND", markdown_path=markdown_file),
            )

        try:
            markdown_text = markdown_path.read_text(encoding="utf-8")
            tables = self.markdown_manager.extract_tables(markdown_text)
            if not tables:
                raise HapeValidationError(
                    code="MARKDOWN_NO_TABLES_FOUND",
                    message=get_markdown_error_message("MARKDOWN_NO_TABLES_FOUND", markdown_path=markdown_file),
                )

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            exported_files: list[str] = []
            for index, (headers, body_rows) in enumerate(tables, start=1):
                dict_rows = self.markdown_manager.table_to_dict_rows(headers, body_rows)
                file_name = f"{markdown_path.stem}_{index:02d}.csv"
                csv_output_path = output_path / file_name
                self.csv_manager.write_csv(str(csv_output_path), dict_rows, delimiter=delimiter)
                exported_files.append(str(csv_output_path))
            return exported_files
        except HapeValidationError:
            raise
        except Exception as exc:
            raise HapeOperationError(
                code="MARKDOWN_EXPORT_FAILED",
                message=get_markdown_error_message("MARKDOWN_EXPORT_FAILED"),
            ) from exc

    def import_csv_table(self, csv_file: str, markdown_file: str, delimiter: str = ",", table_title: str | None = None) -> str:
        self.logger.debug(
            f"import_csv_table(csv_file: {csv_file}, markdown_file: {markdown_file}, delimiter: {delimiter}, table_title: {table_title})"
        )
        self._validate_delimiter(delimiter)
        if not csv_file or not csv_file.strip():
            raise HapeValidationError(
                code="MARKDOWN_CSV_FILE_REQUIRED",
                message=get_markdown_error_message("MARKDOWN_CSV_FILE_REQUIRED"),
            )
        if not markdown_file or not markdown_file.strip():
            raise HapeValidationError(
                code="MARKDOWN_IMPORT_TARGET_REQUIRED",
                message=get_markdown_error_message("MARKDOWN_IMPORT_TARGET_REQUIRED"),
            )
        csv_path = Path(csv_file)
        if not csv_path.exists():
            raise HapeValidationError(
                code="MARKDOWN_CSV_FILE_NOT_FOUND",
                message=get_markdown_error_message("MARKDOWN_CSV_FILE_NOT_FOUND", csv_path=csv_file),
            )
        heading = table_title.strip() if table_title and table_title.strip() else f"## Table: {csv_path.stem}"
        try:
            rows = self.csv_manager.read_csv(str(csv_path), delimiter=delimiter)
            table_text = self.markdown_manager.render_table(rows)
            self.markdown_manager.append_table_block(markdown_file, heading, table_text)
            return markdown_file
        except Exception as exc:
            raise HapeOperationError(
                code="MARKDOWN_IMPORT_FAILED",
                message=get_markdown_error_message("MARKDOWN_IMPORT_FAILED", markdown_path=markdown_file),
            ) from exc

def _demo_export_tables_to_csv() -> None:
    demo_markdown_path = Path("/tmp/hape_markdown_demo.md")
    demo_markdown_path.write_text(
        "\n".join(
            [
                "# Demo",
                "",
                "| name | value |",
                "| --- | --- |",
                "| alpha | 1 |",
                "| beta | 2 |",
            ]
        ),
        encoding="utf-8",
    )
    markdown_service = MarkdownService()
    print(
        markdown_service.export_tables_to_csv(
            markdown_file=str(demo_markdown_path),
            output_dir="/tmp",
        )
    )


def _demo_import_csv_table() -> None:
    markdown_service = MarkdownService()
    print(
        markdown_service.import_csv_table(
            csv_file="/tmp/hape_csv_service_from_json.csv",
            markdown_file="/tmp/hape_markdown_import_demo.md",
        )
    )


if __name__ == "__main__":
    _demo_export_tables_to_csv()
    _demo_import_csv_table()
