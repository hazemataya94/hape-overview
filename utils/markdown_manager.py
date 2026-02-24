import re
from pathlib import Path


class MarkdownManager:
    _TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")

    @staticmethod
    def _is_pipe_row(line: str) -> bool:
        trimmed = line.strip()
        return trimmed.startswith("|") and trimmed.endswith("|") and "|" in trimmed[1:-1]

    @staticmethod
    def _split_pipe_row(line: str) -> list[str]:
        trimmed = line.strip().strip("|")
        return [cell.strip() for cell in trimmed.split("|")]

    def extract_tables(self, markdown_text: str) -> list[tuple[list[str], list[list[str]]]]:
        lines = markdown_text.splitlines()
        tables: list[tuple[list[str], list[list[str]]]] = []
        index = 0
        while index < len(lines):
            current_line = lines[index]
            next_index = index + 1
            if next_index >= len(lines):
                break
            if not self._is_pipe_row(current_line):
                index += 1
                continue
            if not self._TABLE_SEPARATOR_PATTERN.match(lines[next_index]):
                index += 1
                continue

            headers = self._split_pipe_row(current_line)
            body_rows: list[list[str]] = []
            index += 2
            while index < len(lines) and self._is_pipe_row(lines[index]):
                body_rows.append(self._split_pipe_row(lines[index]))
                index += 1
            tables.append((headers, body_rows))
        return tables

    def table_to_dict_rows(self, headers: list[str], body_rows: list[list[str]]) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for row in body_rows:
            normalized_cells = row + ([""] * (len(headers) - len(row)))
            row_dict = {headers[i]: normalized_cells[i] for i in range(len(headers))}
            rows.append(row_dict)
        return rows

    def render_table(self, rows: list[dict[str, str]]) -> str:
        if not rows:
            raise ValueError("Cannot render markdown table from empty rows.")
        headers = list(rows[0].keys())
        header_row = f"| {' | '.join(headers)} |"
        separator_row = f"| {' | '.join(['---'] * len(headers))} |"
        body_lines = []
        for row in rows:
            cells = [self._escape_table_cell(str(row.get(header, ""))) for header in headers]
            body_lines.append(f"| {' | '.join(cells)} |")
        return "\n".join([header_row, separator_row, *body_lines])

    @staticmethod
    def _escape_table_cell(value: str) -> str:
        return value.replace("|", r"\\")

    def append_table_block(self, markdown_path: str, heading: str, table_text: str) -> None:
        path = Path(markdown_path)
        existing_content = ""
        if path.exists():
            existing_content = path.read_text(encoding="utf-8")
        block = f"{heading}\n\n{table_text}\n"
        if existing_content.strip():
            normalized = existing_content.rstrip() + "\n\n" + block
        else:
            normalized = block
        path.write_text(normalized, encoding="utf-8")


def _demo_extract_tables() -> None:
    markdown_manager = MarkdownManager()
    sample = "\n".join(
        [
            "# Demo",
            "",
            "| name | value |",
            "| --- | --- |",
            "| alpha | 1 |",
            "| beta | 2 |",
        ]
    )
    print(markdown_manager.extract_tables(sample))


def _demo_render_table() -> None:
    markdown_manager = MarkdownManager()
    rows = [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]
    print(markdown_manager.render_table(rows))


if __name__ == "__main__":
    _demo_extract_tables()
    _demo_render_table()
