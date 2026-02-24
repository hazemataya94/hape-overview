import argparse
from typing import Any

from services.csv_service import CsvService


class CsvCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "csv",
            help="csv conversion operations.",
        )
        parser.set_defaults(func=CsvCommands.run_help, parser=parser)
        csv_subparsers = parser.add_subparsers(
            dest="csv_command",
            metavar="command",
        )
        csv_subparsers.required = False

        from_json_parser = csv_subparsers.add_parser(
            "from-json",
            help="convert JSON input to CSV file.",
        )
        from_json_parser.add_argument(
            "--json-file",
            required=False,
            default=None,
            help="path to JSON file input.",
        )
        from_json_parser.add_argument(
            "--json-content",
            required=False,
            default=None,
            help="raw JSON array input string.",
        )
        from_json_parser.add_argument(
            "--output-file",
            required=True,
            default=None,
            help="path to CSV output file.",
        )
        from_json_parser.add_argument(
            "--delimiter",
            required=False,
            default=",",
            help="CSV delimiter (default: ,).",
        )
        from_json_parser.set_defaults(func=CsvCommands.run_from_json)

        to_json_parser = csv_subparsers.add_parser(
            "to-json",
            help="convert CSV file to JSON output file.",
        )
        to_json_parser.add_argument(
            "--csv-file",
            required=True,
            default=None,
            help="path to CSV input file.",
        )
        to_json_parser.add_argument(
            "--output-file",
            required=True,
            default=None,
            help="path to JSON output file.",
        )
        to_json_parser.add_argument(
            "--delimiter",
            required=False,
            default=",",
            help="CSV delimiter (default: ,).",
        )
        to_json_parser.set_defaults(func=CsvCommands.run_to_json)

    @staticmethod
    def run_from_json(args: Any) -> None:
        csv_service = CsvService()
        output_file = csv_service.from_json(
            output_file=args.output_file,
            json_file=args.json_file,
            json_content=args.json_content,
            delimiter=args.delimiter,
        )
        print(output_file)

    @staticmethod
    def run_to_json(args: Any) -> None:
        csv_service = CsvService()
        output_file = csv_service.to_json(
            csv_file=args.csv_file,
            output_file=args.output_file,
            delimiter=args.delimiter,
        )
        print(output_file)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
