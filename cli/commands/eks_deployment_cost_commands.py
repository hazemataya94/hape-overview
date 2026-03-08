import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.eks_deployment_cost_service import EksDeploymentCostService


class EksDeploymentCostCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "eks-deployment-cost",
            help="generate EKS Deployment/StatefulSet cost report.",
        )
        parser.set_defaults(func=EksDeploymentCostCommands.run_help, parser=parser)
        eks_cost_subparsers = parser.add_subparsers(
            dest="eks_deployment_cost_command",
            metavar="command",
        )
        eks_cost_subparsers.required = False

        report_parser = eks_cost_subparsers.add_parser(
            "report",
            help="create JSON summary and CSV details for workload costs.",
        )
        report_parser.add_argument(
            "--kube-context",
            required=True,
            default=None,
            help="kube context name.",
        )
        report_parser.add_argument(
            "--kube-config-file",
            required=False,
            default=None,
            help="optional kubeconfig file path.",
        )
        report_parser.add_argument(
            "--aws-profile",
            required=True,
            default=None,
            help="AWS profile name for pricing lookup.",
        )
        report_parser.add_argument(
            "--aws-region",
            required=False,
            default=None,
            help="AWS region code for pricing lookup (defaults to profile region).",
        )
        report_parser.add_argument(
            "--resource-types",
            required=False,
            default=None,
            help="comma-separated resource types. Allowed values: Deployment,StatefulSet.",
        )
        report_parser.add_argument(
            "--namespaces",
            required=False,
            default=None,
            help="comma-separated namespaces. If omitted, all namespaces are used.",
        )
        report_parser.add_argument(
            "--top-n",
            required=False,
            default=20,
            type=int,
            help="number of top hourly-cost workloads in summary (default: 20).",
        )
        report_parser.add_argument(
            "--output-dir",
            required=True,
            default=None,
            help="directory for output report files.",
        )
        report_parser.set_defaults(func=EksDeploymentCostCommands.run_report)

    @staticmethod
    def run_report(args: Any) -> None:
        LocalLogging.bootstrap()
        eks_deployment_cost_service = EksDeploymentCostService()
        outputs = eks_deployment_cost_service.generate_report(
            kube_context=args.kube_context,
            kube_config_file=args.kube_config_file,
            aws_profile=args.aws_profile,
            aws_region=args.aws_region,
            resource_types_csv=args.resource_types,
            namespaces_csv=args.namespaces,
            top_n=args.top_n,
            output_dir=args.output_dir,
        )
        print(json.dumps(outputs, indent=2))

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()


def _demo_register_and_help() -> None:
    parser = argparse.ArgumentParser(prog="hape")
    subparsers = parser.add_subparsers(dest="command")
    EksDeploymentCostCommands.register(subparsers)
    args = parser.parse_args(["eks-deployment-cost"])
    args.func(args)


if __name__ == "__main__":
    _demo_register_and_help()
