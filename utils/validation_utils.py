from typing import Any


class ValidationUtils:
    @staticmethod
    def require_string(config_key: str, config_value: Any) -> str:
        if not isinstance(config_value, str):
            raise ValueError(
                f"{config_key} must be a string. Value is '{config_value}'."
            )
        trimmed_value = config_value.strip()
        if not trimmed_value:
            raise ValueError(f"{config_key} config value is required. Value is not set.")
        if trimmed_value != config_value:
            raise ValueError(f"{config_key} must not contain leading or trailing spaces.")
        return trimmed_value

    @staticmethod
    def validate_domain(config_key: str, config_value: str) -> None:
        if config_value in ["localhost", "127.0.0.1"]:
            return
        if "://" in config_value or "/" in config_value or " " in config_value:
            raise ValueError(f"{config_key} must be a hostname without scheme or path.")
        if "." not in config_value or config_value.startswith(".") or config_value.endswith("."):
            raise ValueError(f"{config_key} must be a valid hostname.")

    @staticmethod
    def validate_email(config_key: str, config_value: str) -> None:
        if " " in config_value or config_value.count("@") != 1:
            raise ValueError(f"{config_key} must be a valid email address.")
        _, domain = config_value.split("@")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError(f"{config_key} must be a valid email address.")

    @staticmethod
    def validate_positive_int(config_key: str, config_value: int) -> None:
        if config_value <= 0:
            raise ValueError(f"{config_key} must be a positive integer.")

    @staticmethod
    def validate_no_spaces(config_key: str, config_value: str) -> None:
        if " " in config_value:
            raise ValueError(f"{config_key} must not contain spaces.")

    @staticmethod
    def validate_min_length_no_spaces(
        config_key: str,
        config_value: str,
        min_length: int,
    ) -> None:
        ValidationUtils.validate_no_spaces(config_key, config_value)
        if len(config_value) < min_length:
            raise ValueError(
                f"{config_key} must be at least {min_length} characters."
            )

    @staticmethod
    def validate_bool(config_key: str, config_value: Any) -> bool:
        if isinstance(config_value, bool):
            return config_value

        if isinstance(config_value, int):
            if config_value in (0, 1):
                return bool(config_value)
            raise ValueError(
                f"{config_key} must be a boolean (true/false) or 0/1. Value is '{config_value}'."
            )

        if isinstance(config_value, str):
            normalized_value = config_value.strip().lower()
            if normalized_value in ("true", "1"):
                return True
            if normalized_value in ("false", "0"):
                return False

        raise ValueError(
            f"{config_key} must be a boolean (true/false) or 0/1. Value is '{config_value}'."
        )
