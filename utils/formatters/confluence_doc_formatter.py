import html
import re

from typing import Optional

import markdown


class ConfluenceDocFormatter:
    _FENCED_BLOCK_PATTERN = re.compile(
        r"```(?P<lang>[^\n`]*)\r?\n(?P<code>.*?)\r?\n```",
        re.DOTALL,
    )

    @classmethod
    def format_markdown_to_storage(cls, markdown_text: str) -> str:
        normalized = cls._replace_fenced_blocks(markdown_text)
        return markdown.markdown(
            normalized,
            extensions=["fenced_code", "tables"],
        )

    @classmethod
    def _replace_fenced_blocks(cls, markdown_text: str) -> str:
        def replace_block(match: re.Match) -> str:
            language = match.group("lang").strip()
            code = match.group("code")
            if language.lower() == "mermaid":
                return cls._mermaid_macro(code)
            return cls._code_macro(code, language or None)

        return cls._FENCED_BLOCK_PATTERN.sub(replace_block, markdown_text)

    @classmethod
    def _mermaid_macro(cls, code: str) -> str:
        return (
            '<ac:structured-macro ac:name="mermaid">'
            "<ac:plain-text-body><![CDATA["
            f"{cls._wrap_cdata(code)}"
            "]]></ac:plain-text-body>"
            "</ac:structured-macro>"
        )

    @classmethod
    def _code_macro(cls, code: str, language: Optional[str]) -> str:
        language_parameter = ""
        if language:
            safe_language = html.escape(language)
            language_parameter = (
                f'<ac:parameter ac:name="language">{safe_language}</ac:parameter>'
            )
        return (
            '<ac:structured-macro ac:name="code">'
            f"{language_parameter}"
            "<ac:plain-text-body><![CDATA["
            f"{cls._wrap_cdata(code)}"
            "]]></ac:plain-text-body>"
            "</ac:structured-macro>"
        )

    @staticmethod
    def _wrap_cdata(text: str) -> str:
        return text.replace("]]>", "]]]]><![CDATA[>")
