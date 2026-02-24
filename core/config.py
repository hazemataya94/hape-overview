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
        "DEPLOYMENTS_ROOT",
        "GITLAB_DOMAIN",
        "GITLAB_TOKEN",
        "GITLAB_DEFAULT_GROUP_ID",
        "KUBERNETES_CONTEXT",
        "ATLASSIAN_DOMAIN",
        "ATLASSIAN_EMAIL",
        "ATLASSIAN_API_KEY",
        "CONFLUENCE_CHANGELOG_PARENT_PAGE_ID",
        "CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID",
        "CONFLUENCE_TEST_PARENT_PAGE_ID",
        "GRAFANA_DOMAIN",
        "GRAFANA_PORT",
        "GRAFANA_TOKEN",
        "GRAFANA_USERNAME",
        "GRAFANA_PASSWORD",
        "GRAFANA_DEPLOYMENTS_SUBPATH",
    ]

    int_config_keys = [
        "GITLAB_DEFAULT_GROUP_ID",
        "CONFLUENCE_CHANGELOG_PARENT_PAGE_ID",
        "CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID",
        "CONFLUENCE_TEST_PARENT_PAGE_ID",
        "GRAFANA_PORT",
    ]

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
    def get_kubernetes_context() -> str:
        context = Config._get_config_value("KUBERNETES_CONTEXT")
        context = ValidationUtils.require_string("KUBERNETES_CONTEXT", context)
        ValidationUtils.validate_no_spaces("KUBERNETES_CONTEXT", context)
        return context

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
        log_level_raw = os.getenv("IDAP_LOG_LEVEL", "DEBUG")
        log_level = log_level_raw.strip().upper()
        allowed_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if log_level not in allowed_levels:
            raise ValueError(
                f"IDAP_LOG_LEVEL must be one of {sorted(allowed_levels)}. Value is '{log_level_raw}'."
            )
        return log_level

    @staticmethod
    def get_enable_log_file() -> bool:
        raw_value = os.getenv("IDAP_ENABLE_LOG_FILE", "0")
        return ValidationUtils.validate_bool("IDAP_ENABLE_LOG_FILE", raw_value)

    @staticmethod
    def get_log_file_path() -> str:
        log_file = os.getenv("IDAP_LOG_FILE", os.path.expanduser("~/.idap/idap.log"))
        return ValidationUtils.require_string("IDAP_LOG_FILE", log_file)

    @staticmethod
    def get_deployments_root(required: bool = True) -> Optional[str]:
        deployments_root = Config._get_config_value("DEPLOYMENTS_ROOT", required=required)
        if deployments_root is None:
            return None
        return ValidationUtils.require_string("DEPLOYMENTS_ROOT", deployments_root)

    @staticmethod
    def get_grafana_domain(required: bool = True) -> Optional[str]:
        grafana_domain = Config._get_config_value("GRAFANA_DOMAIN", required=required)
        if grafana_domain is None:
            return None
        grafana_domain = ValidationUtils.require_string("GRAFANA_DOMAIN", grafana_domain)
        ValidationUtils.validate_domain("GRAFANA_DOMAIN", grafana_domain)
        return grafana_domain

    @staticmethod
    def get_grafana_port(required: bool = False, default: int = 443) -> int:
        grafana_port = Config._get_config_int("GRAFANA_PORT", required=required)
        if grafana_port is None:
            return default
        if grafana_port <= 0 or grafana_port > 65535:
            raise ValueError(f"GRAFANA_PORT must be between 1 and 65535. Value is '{grafana_port}'.")
        return grafana_port

    @staticmethod
    def get_grafana_token(required: bool = True) -> Optional[str]:
        grafana_token = Config._get_config_value("GRAFANA_TOKEN", required=required)
        if grafana_token is None:
            return None
        grafana_token = ValidationUtils.require_string("GRAFANA_TOKEN", grafana_token)
        ValidationUtils.validate_no_spaces("GRAFANA_TOKEN", grafana_token)
        return grafana_token

    @staticmethod
    def get_grafana_username(required: bool = True) -> Optional[str]:
        grafana_username = Config._get_config_value("GRAFANA_USERNAME", required=required)
        if grafana_username is None:
            return None
        grafana_username = ValidationUtils.require_string("GRAFANA_USERNAME", grafana_username)
        ValidationUtils.validate_no_spaces("GRAFANA_USERNAME", grafana_username)
        return grafana_username

    @staticmethod
    def get_grafana_password(required: bool = True) -> Optional[str]:
        grafana_password = Config._get_config_value("GRAFANA_PASSWORD", required=required)
        if grafana_password is None:
            return None
        grafana_password = ValidationUtils.require_string("GRAFANA_PASSWORD", grafana_password)
        return grafana_password

    @staticmethod
    def get_grafana_deployments_subpath(required: bool = True) -> Optional[str]:
        grafana_subpath = Config._get_config_value("GRAFANA_DEPLOYMENTS_SUBPATH", required=required)
        if grafana_subpath is None:
            return None
        return ValidationUtils.require_string("GRAFANA_DEPLOYMENTS_SUBPATH", grafana_subpath)
