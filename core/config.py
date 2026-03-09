######################
######################
# Strict rule:
# You must not include core/logging.py to avoid circular import.
# Config class uses loggers
######################
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from utils.validation_utils import ValidationUtils


class Config:
    _config_loaded = False
    _config_data = None
    _config_path = None
    _dotenv_loaded = False
    default_config_path = os.path.expanduser("~/.hape/config.json")
    default_dotenv_path = Path(__file__).resolve().parents[1] / ".env"

    supported_config_keys = [
        "GITLAB_DOMAIN",
        "GITLAB_TOKEN",
        "GITLAB_DEFAULT_GROUP_ID",
        "ATLASSIAN_DOMAIN",
        "ATLASSIAN_EMAIL",
        "ATLASSIAN_API_KEY",
        "CONFLUENCE_CHANGELOG_PARENT_PAGE_ID",
        "CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID",
        "CONFLUENCE_TEST_PARENT_PAGE_ID",
        "HAPE_EXPORTER_HOST",
        "HAPE_EXPORTER_PORT",
        "HAPE_EXPORTER_REFRESH_SECONDS",
        "HAPE_EDC_KUBE_CONTEXT",
        "HAPE_EDC_AWS_PROFILE",
        "HAPE_EDC_IGNORED_NAMESPACES",
    ]

    int_config_keys = [
        "GITLAB_DEFAULT_GROUP_ID",
        "CONFLUENCE_CHANGELOG_PARENT_PAGE_ID",
        "CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID",
        "CONFLUENCE_TEST_PARENT_PAGE_ID",
        "HAPE_EXPORTER_PORT",
        "HAPE_EXPORTER_REFRESH_SECONDS",
    ]

    @staticmethod
    def _load_config() -> None:
        if Config._config_loaded:
            return
        config_path = Config.get_config_path()
        if not os.path.exists(config_path):
            raise ValueError(
                f"Config file is required. Value is not set. Path: {config_path}"
            )
        with open(config_path, "r", encoding="utf-8") as config_file:
            Config._config_data = json.load(config_file)
        Config._config_loaded = True

    @staticmethod
    def _load_dotenv() -> None:
        if Config._dotenv_loaded:
            return
        if Config.default_dotenv_path.exists():
            load_dotenv(dotenv_path=Config.default_dotenv_path, override=False)
        Config._dotenv_loaded = True

    @staticmethod
    def _get_env_value(config_key: str) -> Optional[str]:
        Config._load_dotenv()
        env_value = os.getenv(config_key)
        if env_value not in (None, ""):
            return env_value
        return None

    @staticmethod
    def _get_config_value(config_key: str, required: bool = True) -> Optional[str]:
        env_value = Config._get_env_value(config_key)
        if env_value is not None:
            return env_value
        Config._load_config()
        if Config._config_data is None:
            raise ValueError("Config file is required. Value is not set.")
        config_value = Config._config_data.get(config_key)
        if config_value not in (None, ""):
            return config_value
        if required:
            raise ValueError(
                f"{config_key} config value is required. Value is not set."
            )
        return None

    @staticmethod
    def _get_config_int(config_key: str, required: bool = True) -> Optional[int]:
        config_value = Config._get_config_value(config_key, required=required)
        if config_value is None:
            return None
        try:
            return int(config_value)
        except ValueError as exc:
            raise ValueError(
                f"{config_key} must be an integer. Value is '{config_value}'."
            ) from exc

    @staticmethod
    def _get_optional_config_value(config_key: str) -> Optional[str]:
        env_value = Config._get_env_value(config_key)
        if env_value is not None:
            return env_value
        config_path = Config.get_config_path()
        if not os.path.exists(config_path):
            return None
        Config._load_config()
        if Config._config_data is None:
            return None
        config_value = Config._config_data.get(config_key)
        if config_value in (None, ""):
            return None
        return str(config_value)

    @staticmethod
    def _get_config_value_with_default(config_key: str, default_value: str) -> str:
        config_value = Config._get_optional_config_value(config_key)
        if config_value is None:
            return default_value
        return config_value

    @staticmethod
    def _get_config_int_with_default(config_key: str, default_value: int) -> int:
        config_value = Config._get_optional_config_value(config_key)
        if config_value is None:
            return default_value
        try:
            return int(config_value)
        except ValueError as exc:
            raise ValueError(
                f"{config_key} must be an integer. Value is '{config_value}'."
            ) from exc

    @staticmethod
    def get_supported_config_keys() -> list[str]:
        return Config.supported_config_keys

    @staticmethod
    def get_int_config_keys() -> list[str]:
        return Config.int_config_keys

    @staticmethod
    def set_config_path(config_path: Optional[str]) -> None:
        if config_path:
            Config._config_path = config_path
            Config._config_loaded = False
            Config._config_data = None

    @staticmethod
    def get_config_path() -> str:
        return Config._config_path or Config.default_config_path

    @staticmethod
    def get_gitlab_token() -> str:
        token = Config._get_config_value("GITLAB_TOKEN")
        token = ValidationUtils.require_string("GITLAB_TOKEN", token)
        ValidationUtils.validate_min_length_no_spaces("GITLAB_TOKEN", token, min_length=10)
        return token

    @staticmethod
    def get_gitlab_domain() -> str:
        domain = Config._get_config_value("GITLAB_DOMAIN")
        domain = ValidationUtils.require_string("GITLAB_DOMAIN", domain)
        ValidationUtils.validate_domain("GITLAB_DOMAIN", domain)
        return domain

    @staticmethod
    def get_gitlab_default_group_id() -> int:
        group_id = Config._get_config_int("GITLAB_DEFAULT_GROUP_ID")
        ValidationUtils.validate_positive_int("GITLAB_DEFAULT_GROUP_ID", group_id)
        return group_id

    @staticmethod
    def get_atlassian_domain() -> str:
        domain = Config._get_config_value("ATLASSIAN_DOMAIN")
        domain = ValidationUtils.require_string("ATLASSIAN_DOMAIN", domain)
        ValidationUtils.validate_domain("ATLASSIAN_DOMAIN", domain)
        return domain

    @staticmethod
    def get_atlassian_email() -> str:
        email = Config._get_config_value("ATLASSIAN_EMAIL")
        email = ValidationUtils.require_string("ATLASSIAN_EMAIL", email)
        ValidationUtils.validate_email("ATLASSIAN_EMAIL", email)
        return email

    @staticmethod
    def get_atlassian_api_key() -> str:
        api_key = Config._get_config_value("ATLASSIAN_API_KEY")
        api_key = ValidationUtils.require_string("ATLASSIAN_API_KEY", api_key)
        ValidationUtils.validate_min_length_no_spaces(
            "ATLASSIAN_API_KEY",
            api_key,
            min_length=10,
        )
        return api_key

    @staticmethod
    def get_changelog_parent_page_id() -> int:
        parent_id = Config._get_config_int("CONFLUENCE_CHANGELOG_PARENT_PAGE_ID")
        ValidationUtils.validate_positive_int(
            "CONFLUENCE_CHANGELOG_PARENT_PAGE_ID",
            parent_id,
        )
        return parent_id

    @staticmethod
    def get_changelog_entry_page_template_id() -> int:
        template_id = Config._get_config_int("CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID")
        ValidationUtils.validate_positive_int(
            "CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID",
            template_id,
        )
        return template_id

    @staticmethod
    def get_test_parent_page_id() -> int:
        parent_id = Config._get_config_int("CONFLUENCE_TEST_PARENT_PAGE_ID")
        ValidationUtils.validate_positive_int("CONFLUENCE_TEST_PARENT_PAGE_ID", parent_id)
        return parent_id

    @staticmethod
    def get_log_level() -> str:
        log_level_raw = os.getenv("HAPE_LOG_LEVEL", "DEBUG")
        log_level = log_level_raw.strip().upper()
        allowed_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if log_level not in allowed_levels:
            raise ValueError(
                f"HAPE_LOG_LEVEL must be one of {sorted(allowed_levels)}. Value is '{log_level_raw}'."
            )
        return log_level

    @staticmethod
    def get_enable_log_file() -> bool:
        raw_value = os.getenv("HAPE_ENABLE_LOG_FILE", "0")
        return ValidationUtils.validate_bool("HAPE_ENABLE_LOG_FILE", raw_value)

    @staticmethod
    def get_log_file_path() -> str:
        log_file = os.getenv("HAPE_LOG_FILE", os.path.expanduser("~/.hape/hape.log"))
        return ValidationUtils.require_string("HAPE_LOG_FILE", log_file)

    @staticmethod
    def get_exporter_host() -> str:
        host = Config._get_config_value_with_default("HAPE_EXPORTER_HOST", "0.0.0.0")
        return ValidationUtils.require_string("HAPE_EXPORTER_HOST", host)

    @staticmethod
    def get_exporter_port() -> int:
        port = Config._get_config_int_with_default("HAPE_EXPORTER_PORT", 9117)
        ValidationUtils.validate_positive_int("HAPE_EXPORTER_PORT", port)
        return port

    @staticmethod
    def get_exporter_refresh_seconds() -> int:
        refresh_seconds = Config._get_config_int_with_default("HAPE_EXPORTER_REFRESH_SECONDS", 300)
        ValidationUtils.validate_positive_int("HAPE_EXPORTER_REFRESH_SECONDS", refresh_seconds)
        return refresh_seconds

    @staticmethod
    def get_edc_kube_context() -> str:
        kube_context = Config._get_optional_config_value("HAPE_EDC_KUBE_CONTEXT")
        if kube_context is None:
            return ""
        return ValidationUtils.require_string("HAPE_EDC_KUBE_CONTEXT", kube_context)

    @staticmethod
    def get_edc_aws_profile() -> str:
        aws_profile = Config._get_optional_config_value("HAPE_EDC_AWS_PROFILE")
        if aws_profile is None:
            return ""
        return ValidationUtils.require_string("HAPE_EDC_AWS_PROFILE", aws_profile)

    @staticmethod
    def get_edc_ignored_namespaces_csv() -> str:
        default_value = "kube-system,kube-node-lease,kube-public,local-path-storage"
        ignored_namespaces_csv = Config._get_config_value_with_default("HAPE_EDC_IGNORED_NAMESPACES", default_value)
        return ValidationUtils.require_string("HAPE_EDC_IGNORED_NAMESPACES", ignored_namespaces_csv)

