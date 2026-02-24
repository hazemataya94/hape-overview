import re

from typing import List


class JiraCommentFormatter:
    _FENCED_BLOCK_PATTERN = re.compile(
        r"```(?P<lang>[^\n`]*)\r?\n(?P<code>.*?)\r?\n```",
        re.DOTALL,
    )
    _MD_TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?[\s:-]+\|[\s\|:-]*$")
    _HEADING_PATTERN = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+)$")
    _INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")

    @classmethod
    def format_markdown_to_jira_wiki(cls, markdown_text: str) -> str:
        blocks, placeholders = cls._extract_fenced_blocks(markdown_text)
        lines = cls._convert_tables(markdown_text, placeholders)
        formatted_lines: List[str] = []
        for line in lines:
            formatted_lines.append(cls._format_jira_line(line))
        return cls._restore_fenced_blocks("\n".join(formatted_lines), blocks)

    @classmethod
    def format_markdown_to_jira_wiki_with_mermaid(
        cls,
        markdown_text: str,
    ) -> tuple[str, List[str]]:
        code_blocks, mermaid_blocks, normalized, placeholders = (
            cls._extract_fenced_blocks_with_mermaid(markdown_text)
        )
        lines = cls._convert_tables(normalized, placeholders)
        formatted_lines: List[str] = []
        for line in lines:
            formatted_lines.append(cls._format_jira_line(line))
        comment_body = cls._restore_fenced_blocks(
            "\n".join(formatted_lines),
            code_blocks,
        )
        return comment_body, mermaid_blocks

    @classmethod
    def _extract_fenced_blocks(cls, markdown_text: str) -> tuple[List[str], List[str]]:
        blocks: List[str] = []
        placeholders: List[str] = []

        def replace_block(match: re.Match) -> str:
            language = match.group("lang").strip() or ""
            code = match.group("code")
            blocks.append(cls._jira_code_block(code, language))
            placeholder = f"@@JIRA_CODE_BLOCK_{len(blocks) - 1}@@"
            placeholders.append(placeholder)
            return placeholder

        normalized = cls._FENCED_BLOCK_PATTERN.sub(replace_block, markdown_text)
        return blocks, normalized.splitlines()

    @classmethod
    def _extract_fenced_blocks_with_mermaid(
        cls,
        markdown_text: str,
    ) -> tuple[List[str], List[str], str, List[str]]:
        code_blocks: List[str] = []
        mermaid_blocks: List[str] = []
        placeholders: List[str] = []

        def replace_block(match: re.Match) -> str:
            language = match.group("lang").strip()
            code = match.group("code")
            if language.lower() == "mermaid":
                placeholder = f"@@JIRA_MERMAID_{len(mermaid_blocks)}@@"
                mermaid_blocks.append(code)
            else:
                placeholder = f"@@JIRA_CODE_BLOCK_{len(code_blocks)}@@"
                code_blocks.append(cls._jira_code_block(code, language or ""))
            placeholders.append(placeholder)
            return placeholder

        normalized = cls._FENCED_BLOCK_PATTERN.sub(replace_block, markdown_text)
        return code_blocks, mermaid_blocks, normalized, placeholders

    @classmethod
    def _restore_fenced_blocks(cls, text: str, blocks: List[str]) -> str:
        for index, block in enumerate(blocks):
            placeholder = f"@@JIRA_CODE_BLOCK_{index}@@"
            text = text.replace(placeholder, block)
        return text

    @classmethod
    def _jira_code_block(cls, code: str, language: str) -> str:
        language = language.strip()
        if language:
            return f"{{code:{language}}}\n{code}\n{{code}}"
        return f"{{code}}\n{code}\n{{code}}"

    @classmethod
    def _convert_tables(cls, markdown_text: str, placeholders: List[str]) -> List[str]:
        lines = markdown_text.splitlines()
        output: List[str] = []
        index = 0
        placeholder_set = set(placeholders)
        while index < len(lines):
            line = lines[index]
            if line in placeholder_set:
                output.append(line)
                index += 1
                continue

            if (
                "|" in line
                and index + 1 < len(lines)
                and cls._MD_TABLE_SEPARATOR_PATTERN.match(lines[index + 1])
            ):
                header_cells = cls._split_md_table_row(line)
                output.append(cls._format_jira_header_row(header_cells))
                index += 2
                while index < len(lines) and "|" in lines[index]:
                    body_cells = cls._split_md_table_row(lines[index])
                    output.append(cls._format_jira_body_row(body_cells))
                    index += 1
                continue

            output.append(line)
            index += 1
        return output

    @classmethod
    def _split_md_table_row(cls, line: str) -> List[str]:
        trimmed = line.strip().strip("|")
        return [cell.strip() for cell in trimmed.split("|")]

    @staticmethod
    def _format_jira_header_row(cells: List[str]) -> str:
        return "|| " + " || ".join(cells) + " ||"

    @staticmethod
    def _format_jira_body_row(cells: List[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    @classmethod
    def _format_jira_line(cls, line: str) -> str:
        if line.startswith("@@JIRA_CODE_BLOCK_") or line.startswith("@@JIRA_MERMAID_"):
            return line
        heading_match = cls._HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group("level"))
            title = heading_match.group("title").strip()
            return f"h{level}. {title}"

        if line.lstrip().startswith(("- ", "* ")):
            return cls._format_jira_list_item(line, bullet=True)

        ordered_match = re.match(r"^(?P<indent>\s*)\d+\.\s+(?P<item>.+)$", line)
        if ordered_match:
            return cls._format_jira_list_item(line, bullet=False)

        return cls._INLINE_CODE_PATTERN.sub(r"{{\1}}", line)

    @staticmethod
    def _format_jira_list_item(line: str, bullet: bool) -> str:
        indent = len(line) - len(line.lstrip(" "))
        level = max(1, indent // 2 + 1)
        marker = "*" if bullet else "#"
        content = line.lstrip(" ")
        content = (
            content[2:] if content.startswith(("- ", "* ")) else content.split(". ", 1)[-1]
        )
        return f"{marker * level} {content}"
