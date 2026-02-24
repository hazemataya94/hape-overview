import csv
import json
from pathlib import Path
from typing import Any


class CsvManager:

    @staticmethod
    def _normalize_row(fieldnames: list[str], row: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for field in fieldnames:
            normalized[field] = row.get(field, "")
        return normalized

    def read_csv(self, csv_path: str, delimiter: str = ",") -> list[dict[str, str]]:
        self.logger.debug(f"read_csv(csv_path: {csv_path}, delimiter: {delimiter})")
        with open(csv_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            rows: list[dict[str, str]] = []
            for row in reader:
                clean_row = {str(key).strip(): (value or "").strip() for key, value in row.items()}
                rows.append(clean_row)
        return rows

    def write_csv(self, csv_path: str, rows: list[dict[str, Any]], delimiter: str = ",") -> None:
        self.logger.debug(f"write_csv(csv_path: {csv_path}, delimiter: {delimiter}, row_count: {len(rows)})")
        if not rows:
            raise ValueError("CSV rows are empty.")
        fieldnames = list(rows[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            for row in rows:
                writer.writerow(self._normalize_row(fieldnames, row))

    def parse_json_rows(self, json_text: str) -> list[dict[str, Any]]:
        self.logger.debug("parse_json_rows()")
        data = json.loads(json_text)
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects.")
        if not data:
            raise ValueError("JSON array is empty.")
        normalized_rows: list[dict[str, Any]] = []
        for row in data:
            if not isinstance(row, dict):
                raise ValueError("Each JSON array item must be an object.")
            normalized_rows.append(row)
        return normalized_rows

    def read_json_rows(self, json_path: str) -> list[dict[str, Any]]:
        self.logger.debug(f"read_json_rows(json_path: {json_path})")
        content = Path(json_path).read_text(encoding="utf-8")
        return self.parse_json_rows(content)

    def write_json(self, output_path: str, rows: list[dict[str, str]]) -> None:
        self.logger.debug(f"write_json(output_path: {output_path}, row_count: {len(rows)})")
        Path(output_path).write_text(json.dumps(rows, indent=4), encoding="utf-8")


def _demo_read_write_csv() -> None:
    csv_manager = CsvManager()
    sample_rows = [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]
    csv_manager.write_csv("/tmp/idap_csv_manager_demo.csv", sample_rows)
    print(csv_manager.read_csv("/tmp/idap_csv_manager_demo.csv"))


def _demo_json_rows() -> None:
    csv_manager = CsvManager()
    json_rows = csv_manager.parse_json_rows('[{"name":"alpha","value":1},{"name":"beta","value":2}]')
    print(json_rows)


if __name__ == "__main__":
    _demo_read_write_csv()
    _demo_json_rows()
