import argparse
from typing import Any

from core.logging import LocalLogging
from services.config_service import ConfigService


class ConfigCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "config",
            help="config file operations.",
        )
        parser.set_defaults(func=ConfigCommands.run_help, parser=parser)
        config_subparsers = parser.add_subparsers(
            dest="config_command",
            metavar="command",
        )
        config_subparsers.required = False

        init_parser = config_subparsers.add_parser(
            "init-config-file",
            help="generate config.json from .env.",
        )
        init_parser.add_argument(
            "--dot-env-file",
            required=False,
            default=None,
            help="path to .env file (optional). If omitted, use environment variables.",
        )
        init_parser.set_defaults(func=ConfigCommands.run_init_config_file)

    @staticmethod
    def run_init_config_file(args: Any) -> None:
        LocalLogging.bootstrap()
        config_service = ConfigService()
        config_path = config_service.init_config_file(
            config_path=args.config_file_path,
            dot_env_file=args.dot_env_file,
        )
        print(config_path)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
