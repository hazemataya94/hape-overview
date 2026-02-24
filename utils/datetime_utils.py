import re

from datetime import datetime


class DatetimeUtils:
    @staticmethod
    def normalize_date_format(date: str, reversed: bool = False) -> str:
        valid_date_regex = re.compile(
            r"\b(0[1-9]|[12]\d|3[01])([./-])(0[1-9]|1[0-2])\2(\d{4})\b"
        )
        date_like_regex = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b")
        if reversed:
            normalized = valid_date_regex.sub(r"\4-\3-\1", date)
        else:
            normalized = valid_date_regex.sub(r"\1-\3-\4", date)
        if not date_like_regex.search(normalized):
            raise ValueError(
                "Invalid date format; expected dd-mm-yyyy, dd.mm.yyyy or dd/mm/yyyy"
            )

        return normalized

    @staticmethod
    def date_to_isoformat(date_input: str) -> str:
        normalized = DatetimeUtils.normalize_date_format(date_input)
        return datetime.strptime(normalized, "%d-%m-%Y").isoformat()

    @staticmethod
    def parse_iso_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
