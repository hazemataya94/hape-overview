import os
from typing import Any, Dict, Optional

from dotenv import dotenv_values

from core.config import Config
from core.errors.exceptions import HapeOperationError, HapeValidationError
from core.errors.messages.config_error_messages import get_config_error_message
from utils.file_manager import FileManager


class ConfigService:
    def __init__(self) -> None:
        self.file_manager = FileManager()
        
    @staticmethod
    def _get_parent_dir(path: str) -> str:
        parent_dir = os.path.dirname(path)
        return parent_dir or "."

    def _build_config_from_env(self, dot_env_file: Optional[str] = None) -> Dict[str, Any]:
        if dot_env_file:
            env_values = dotenv_values(dot_env_file)
            if not env_values:
                raise HapeValidationError(
                    code="CONFIG_ENV_FILE_INVALID",
                    message=get_config_error_message(
                        "CONFIG_ENV_FILE_INVALID",
                        dot_env_file=dot_env_file,
                    ),
                )
        else:
            env_values = dict(os.environ)

        config_data: Dict[str, Any] = {}
        for key in Config.get_supported_config_keys():
            value = env_values.get(key)
            if value in (None, ""):
                continue
            if key in Config.get_int_config_keys():
                try:
                    config_data[key] = int(value)
                except ValueError as exc:
                    raise HapeValidationError(
                        code="CONFIG_ENV_INT_REQUIRED",
                        message=get_config_error_message(
                            "CONFIG_ENV_INT_REQUIRED",
                            config_key=key,
                        ),
                    ) from exc
            else:
                config_data[key] = value
        return config_data
        
    def init_config_file(self, config_path: Optional[str] = None, dot_env_file: Optional[str] = None) -> str:
        resolved_path = config_path or Config.get_config_path()
        parent_dir = self._get_parent_dir(resolved_path)
        try:
            self.file_manager.create_directory(parent_dir)
        except PermissionError as exc:
            raise HapeOperationError(
                code="CONFIG_PERMISSION_DENIED",
                message=get_config_error_message(
                    "CONFIG_PERMISSION_DENIED",
                    parent_dir=parent_dir,
                ),
            ) from exc
        config_data = self._build_config_from_env(dot_env_file=dot_env_file)
        self.file_manager.write_json_file(resolved_path, config_data)
        return resolved_path
