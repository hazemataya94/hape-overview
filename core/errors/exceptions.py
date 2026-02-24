from dataclasses import dataclass


@dataclass
class HapeError(Exception):
    code: str
    message: str
    exit_code: int = 1

    def __post_init__(self) -> None:
        super().__init__(self.message)


class HapeValidationError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 2) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code)


class HapeOperationError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 3) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code)


class HapeExternalError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 3) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code)


class HapeUserAbortError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 130) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code)


if __name__ == "__main__":
    print(HapeValidationError(code="HAPE_EXAMPLE", message="Example validation error."))
