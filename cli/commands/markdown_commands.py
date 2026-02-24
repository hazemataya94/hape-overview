import argparse
import json
from typing import Any

from services.markdown_service import MarkdownService


class MarkdownCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "markdown",
            help="markdown table import/export operations.",
        )
        parser.set_defaults(func=MarkdownCommands.run_help, parser=parser)
        markdown_subparsers = parser.add_subparsers(
            dest="markdown_command",
            metavar="command",
        )
        markdown_subparsers.required = False

        export_parser = markdown_subparsers.add_parser(
            "export-tables-to-csv",
            help="export markdown pipe tables to CSV files.",
        )
        export_parser.add_argument(
            "--md-file",
            required=True,
            default=None,
            help="path to markdown file input.",
        )
        export_parser.add_argument(
            "--output-dir",
            required=True,
            default=None,
            help="directory for generated CSV files.",
        )
        export_parser.add_argument(
            "--delimiter",
            required=False,
            default=",",
            help="CSV delimiter (default: ,).",
        )
        export_parser.set_defaults(func=MarkdownCommands.run_export_tables_to_csv)

        import_parser = markdown_subparsers.add_parser(
            "import-csv-table",
            help="append CSV content as markdown table.",
        )
        import_parser.add_argument(
            "--csv-file",
            required=True,
            default=None,
            help="path to CSV file input.",
        )
        import_parser.add_argument(
            "--md-file",
            required=True,
            default=None,
            help="path to markdown file target.",
        )
        import_parser.add_argument(
            "--delimiter",
            required=False,
            default=",",
            help="CSV delimiter (default: ,).",
        )
        import_parser.add_argument(
            "--table-title",
            required=False,
            default=None,
            help="optional markdown heading before table content.",
        )
        import_parser.set_defaults(func=MarkdownCommands.run_import_csv_table)

    @staticmethod
    def run_export_tables_to_csv(args: Any) -> None:
        markdown_service = MarkdownService()
        output_files = markdown_service.export_tables_to_csv(
            markdown_file=args.md_file,
            output_dir=args.output_dir,
            delimiter=args.delimiter,
        )
        print(json.dumps(output_files, indent=4))

    @staticmethod
    def run_import_csv_table(args: Any) -> None:
        markdown_service = MarkdownService()
        output_path = markdown_service.import_csv_table(
            csv_file=args.csv_file,
            markdown_file=args.md_file,
            delimiter=args.delimiter,
            table_title=args.table_title,
        )
        print(output_path)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
