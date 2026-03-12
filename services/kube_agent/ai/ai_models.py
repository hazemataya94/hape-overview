from dataclasses import dataclass, field


@dataclass(frozen=True)
class AiExplanation:
    summary: str
    possible_root_cause: str
    reasoning: str
    debugging_steps: list[str] = field(default_factory=list)
    suggested_fixes: list[str] = field(default_factory=list)


if __name__ == "__main__":
    print(AiExplanation(summary="Example summary", possible_root_cause="Example cause", reasoning="Example reasoning"))
