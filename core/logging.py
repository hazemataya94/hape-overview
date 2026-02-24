import os
import sys
import shutil
import logging
import logging.config
import json
from typing import Optional
from threading import Lock
from datetime import datetime
from pythonjsonlogger import jsonlogger
from core.config import Config

GLOBAL_LOGGER_NAME = "hape.global"


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def parse(self):
        return [
            "timestamp",
            "level",
            "name",
            "message",
            "module",
            "funcName",
            "lineno",
        ]


LOGGING_CONFIG = (
    '{"version":1,"disable_existing_loggers":false,'
    '"formatters":{"standard":{"format":"%(asctime)s %(levelname)s - '
    '%(name)s - %(message)s"}},'
    '"handlers":{"console":{"class":"logging.StreamHandler",'
    '"formatter":"standard","level":"{{log_level}}"}},"root":'
    '{"handlers":["console"],"level":"{{log_level}}"}}'
)


class LocalLogging:
    _bootstrap_lock = Lock()
    _is_bootstrapped = False
    _log_file_path_override: Optional[str] = None
    _force_enable_log_file = False

    @staticmethod
    def _apply_logging_config() -> None:
        logging.getLogger("kubernetes").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("s3transfer").setLevel(logging.WARNING)

        log_level = Config.get_log_level()
        enable_log_file = Config.get_enable_log_file() or LocalLogging._force_enable_log_file

        logging_config_json = LOGGING_CONFIG.replace("{{log_level}}", log_level)
        logging_config = json.loads(logging_config_json)
        logging_config["formatters"]["json"] = {
            "()": CustomJsonFormatter,
            "fmt": (
                "%(timestamp)s %(level)s %(name)s %(message)s %(module)s "
                "%(funcName)s %(lineno)d"
            ),
        }

        if enable_log_file:
            log_file = LocalLogging._log_file_path_override or Config.get_log_file_path()
            logging_config["handlers"]["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": log_level,
                "filename": log_file,
                "maxBytes": 10_485_760,
                "backupCount": 5,
            }
            logging_config["root"]["handlers"].append("file")

        logging.config.dictConfig(logging_config)

    @staticmethod
    def get_logger(name: str = GLOBAL_LOGGER_NAME) -> logging.Logger:
        logger = logging.getLogger(name)
        if "--version" in sys.argv:
            logging.disable(logging.CRITICAL)
        return logger

    @staticmethod
    def rotate_log_file(log_file: str) -> None:
        if os.path.exists(log_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name, file_ext = os.path.splitext(log_file)
            file_ext = ".log"
            new_log_file = f"{file_name}_{timestamp}{file_ext}"
            shutil.move(log_file, new_log_file)

    @staticmethod
    def set_log_file_path(log_file_path: str) -> None:
        normalized_path = log_file_path.strip()
        if not normalized_path:
            raise ValueError("log_file_path is required.")
        with LocalLogging._bootstrap_lock:
            LocalLogging._log_file_path_override = normalized_path
            LocalLogging._force_enable_log_file = True
            if LocalLogging._is_bootstrapped:
                LocalLogging._apply_logging_config()

    @staticmethod
    def reset_log_file_path() -> None:
        with LocalLogging._bootstrap_lock:
            LocalLogging._log_file_path_override = None
            LocalLogging._force_enable_log_file = False
            if LocalLogging._is_bootstrapped:
                LocalLogging._apply_logging_config()

    @staticmethod
    def bootstrap() -> None:
        if LocalLogging._is_bootstrapped:
            return

        with LocalLogging._bootstrap_lock:
            if LocalLogging._is_bootstrapped:
                return
            LocalLogging._apply_logging_config()
            logger = LocalLogging.get_logger("hape.core_logging")
            logger.info("Application started!")
            LocalLogging._is_bootstrapped = True
