from services.kube_agent.ai.ai_models import AiExplanation


class AiResponseParser:
    @staticmethod
    def _extract_list(value: str) -> list[str]:
        if not value.strip():
            return []
        return [item.strip() for item in value.split(";") if item.strip()]

    def parse(self, raw_response: dict[str, str]) -> AiExplanation:
        return AiExplanation(
            summary=str(raw_response.get("summary", "")).strip(),
            possible_root_cause=str(raw_response.get("possible_root_cause", "")).strip(),
            reasoning=str(raw_response.get("reasoning", "")).strip(),
            debugging_steps=self._extract_list(str(raw_response.get("debugging_steps", ""))),
            suggested_fixes=self._extract_list(str(raw_response.get("suggested_fixes", ""))),
        )


if __name__ == "__main__":
    print(AiResponseParser())
