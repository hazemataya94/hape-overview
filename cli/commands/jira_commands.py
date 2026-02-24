import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.jira_service import JiraService


class JiraCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "jira",
            help="fetch Jira issue data, remote links, or add comments.",
        )
        parser.set_defaults(func=JiraCommands.run_help, parser=parser)
        jira_subparsers = parser.add_subparsers(
            dest="jira_command",
            metavar="command",
        )
        jira_subparsers.required = False

        convert_parser = jira_subparsers.add_parser(
            "md-to-comment",
            help="add a Jira comment from a markdown file.",
        )
        convert_parser.add_argument(
            "--issue-key",
            required=True,
            default=None,
            help="issue key.",
        )
        convert_parser.add_argument(
            "--md-path",
            required=True,
            default=None,
            help="path to markdown file to post as a comment.",
        )
        convert_parser.set_defaults(func=JiraCommands.run_convert_md_to_comment)

    @staticmethod
    def run_convert_md_to_comment(args: Any) -> None:
        LocalLogging.bootstrap()
        jira_service = JiraService()
        data = jira_service.add_comment_from_markdown(
            issue_key=args.issue_key,
            markdown_path=args.md_path,
        )
        issue_url = jira_service.get_issue_url(args.issue_key)
        print(issue_url)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()
