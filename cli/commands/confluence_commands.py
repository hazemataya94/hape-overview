import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.confluence_service import ConfluenceService


class ConfluenceCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "confluence",
            help="confluence page operations.",
        )
        parser.set_defaults(func=ConfluenceCommands.run_help, parser=parser)
        confluence_subparsers = parser.add_subparsers(
            dest="confluence_command",
            metavar="command",
        )
        confluence_subparsers.required = False

        get_parser = confluence_subparsers.add_parser(
            "get-page",
            help="fetch a confluence page by ID.",
        )
        get_parser.add_argument(
            "--page-id",
            required=True,
            default=None,
            help="page ID (e.g., 123456).",
        )
        get_parser.add_argument(
            "--expand",
            required=False,
            default="body.storage",
            help="confluence expand parameter (default: body.storage).",
        )
        get_parser.set_defaults(func=ConfluenceCommands.run_get_page)

        create_parser = confluence_subparsers.add_parser(
            "create-page",
            help="create a confluence page under a parent page.",
        )
        create_parser.add_argument(
            "--parent-page-id",
            required=True,
            default=None,
            help="parent page ID (e.g., 123456).",
        )
        create_parser.add_argument(
            "--page-title",
            required=True,
            default=None,
            help="page title.",
        )
        create_parser.add_argument(
            "--page-body",
            required=True,
            default=None,
            help="page body (storage format).",
        )
        create_parser.add_argument(
            "--space-key",
            required=True,
            default=None,
            help="confluence space key.",
        )
        create_parser.add_argument(
            "--labels",
            required=False,
            nargs="*",
            default=None,
            help="confluence labels (optional).",
        )
        create_parser.set_defaults(func=ConfluenceCommands.run_create_page)

        readme_parser = confluence_subparsers.add_parser(
            "md-to-page",
            help="create a confluence page from a markdown file.",
        )
        readme_parser.add_argument(
            "--parent-page-id",
            required=False,
            default=None,
            help="parent page ID (default: CONFLUENCE_TEST_PARENT_PAGE_ID).",
        )
        readme_parser.add_argument(
            "--md-path",
            required=False,
            default="README.md",
            help="path to markdown file (default: README.md).",
        )
        readme_parser.add_argument(
            "--page-title",
            required=False,
            default=None,
            help="page title (default: derived from README).",
        )
        readme_parser.add_argument(
            "--space-key",
            required=True,
            default=None,
            help="confluence space key.",
        )
        readme_parser.add_argument(
            "--labels",
            required=False,
            nargs="*",
            default=None,
            help="confluence labels (optional).",
        )
        readme_parser.set_defaults(func=ConfluenceCommands.run_readme_to_page)

    @staticmethod
    def run_get_page(args: Any) -> None:
        confluence_service = ConfluenceService()
        page = confluence_service.get_page(args.page_id, expand=args.expand)
        print(json.dumps(page, indent=4))

    @staticmethod
    def run_create_page(args: Any) -> None:
        confluence_service = ConfluenceService()
        page = confluence_service.create_page(
            parent_page_id=args.parent_page_id,
            page_title=args.page_title,
            page_body=args.page_body,
            space_key=args.space_key,
            labels=args.labels,
        )
        print(confluence_service.get_page_link(page["id"], args.space_key))

    @staticmethod
    def run_readme_to_page(args: Any) -> None:
        confluence_service = ConfluenceService()
        page = confluence_service.create_page_from_markdown(
            parent_page_id=args.parent_page_id,
            readme_path=args.md_path,
            page_title=args.page_title,
            space_key=args.space_key,
            labels=args.labels,
        )
        print(confluence_service.get_page_link(page["id"], args.space_key))

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
