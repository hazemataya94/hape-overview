from services.kube_agent.checks.base_check import BaseCheck
from services.kube_agent.checks.packs.image_pull_checks import ErrImagePullCheck, ImagePullBackOffCheck
from services.kube_agent.checks.packs.node_condition_checks import DiskPressureCheck, MemoryPressureCheck, NodeNotReadyCheck, PidPressureCheck
from services.kube_agent.checks.packs.pod_pending_checks import FailedSchedulingCheck, ImagePullFailureCheck, InsufficientResourceCheck, PvcBindingCheck, TaintMismatchCheck
from services.kube_agent.checks.packs.pod_restart_checks import EvictionCheck, OomKillCheck, ProbeFailureCheck, UnexpectedExitCodeCheck
from services.kube_agent.checks.packs.probe_failure_checks import LivenessProbeFailureCheck, ReadinessProbeFailureCheck
from services.kube_agent.checks.packs.rollout_regression_checks import ConfigChangeCorrelationCheck, DeploymentRevisionChangeCheck, ImageChangeCheck


class DiagnosticCheckRegistry:
    def get_checks(self) -> list[BaseCheck]:
        return [
            OomKillCheck(), ProbeFailureCheck(), EvictionCheck(), UnexpectedExitCodeCheck(),
            FailedSchedulingCheck(), InsufficientResourceCheck(), TaintMismatchCheck(), PvcBindingCheck(), ImagePullFailureCheck(),
            MemoryPressureCheck(), DiskPressureCheck(), PidPressureCheck(), NodeNotReadyCheck(),
            DeploymentRevisionChangeCheck(), ImageChangeCheck(), ConfigChangeCorrelationCheck(),
            ReadinessProbeFailureCheck(), LivenessProbeFailureCheck(),
            ImagePullBackOffCheck(), ErrImagePullCheck(),
        ]


if __name__ == "__main__":
    print(len(DiagnosticCheckRegistry().get_checks()))
