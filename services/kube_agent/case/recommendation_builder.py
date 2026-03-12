from services.kube_agent.checks.diagnostic_check_models import CheckResult


class RecommendationBuilder:
    DEFAULT_RECOMMENDATIONS = {
        "oom-kill": "Increase memory request/limit or reduce memory pressure in workload.",
        "failed-scheduling": "Review node capacity, pod resource requests, and scheduler constraints.",
        "node-not-ready": "Inspect node kubelet status, networking, and underlying node health.",
        "image-pull-backoff": "Verify image repository, tag, and image pull credentials.",
        "err-image-pull": "Verify image repository accessibility and registry credentials.",
    }

    def _build_recommendation(self, check_result: CheckResult) -> str | None:
        if check_result.status != "matched":
            return None
        return self.DEFAULT_RECOMMENDATIONS.get(check_result.check_name)

    def build(self, check_results: list[CheckResult]) -> list[str]:
        recommendations: list[str] = []
        for check_result in check_results:
            recommendation = self._build_recommendation(check_result=check_result)
            if recommendation:
                recommendations.append(recommendation)
        return recommendations


if __name__ == "__main__":
    print(RecommendationBuilder())
