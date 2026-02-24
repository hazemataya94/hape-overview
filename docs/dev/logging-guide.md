# Logging Guide

## Purpose
Define how logging is initialized and how classes should emit logs in HAPE.

## Logging Source of Truth
- Use `core/logging.py` as the only logging setup entrypoint.
- Do not configure Python logging directly in services, clients, or commands.
- Use `LocalLogging.get_logger(...)` to create loggers.

## Bootstrap Behavior
- Initialize logging with `LocalLogging.bootstrap()`.
- `bootstrap()` is idempotent and runs only once, even if called many times.
- It is safe for multiple modules to call it.
- Default log level is `DEBUG`; override via `HAPE_LOG_LEVEL` env (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- File logging is disabled by default; enable with `HAPE_ENABLE_LOG_FILE=1` and optionally set `HAPE_LOG_FILE` (default `~/.hape/hape.log`). Uses rotating handler (10MB, 5 backups).

## Where to Call Bootstrap
- CLI command entry methods can call `LocalLogging.bootstrap()` before work starts.
- Central handlers (for example error handling) may call it defensively.
- Do not duplicate custom logging setup in each module.

## Logger Naming Convention
- Use `hape.<class_name_snake_case>` for class loggers.
- Example:
  - `JiraService` -> `hape.jira_service`
  - `EKSNodeRotationService` -> `hape.eks_node_rotation_service`

## Class Pattern
Use this pattern in services and clients:

```python
from core.logging import LocalLogging


class MyService:
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.my_service")

    def run(self, item_id: str) -> None:
        self.logger.debug(f"Starting run for item_id={item_id}")
        # business logic
        self.logger.debug(f"Completed run for item_id={item_id}")
```

## Debug Logging Guidelines
- Log at method boundaries for important workflows:
  - start of operation
  - important branch decisions
  - completion of operation
- Add log method entry with key parameters in client, service, and utils classes, like the following:
```python
def function_name(arg1: type1, arg2: type2) -> type_return:
  self.logger.debug(f"function_name(arg1: {arg1}, arg2: {arg2})")
```
- Keep logs concise and actionable.
- Do not log secrets, tokens, API keys, or credentials.
- Prefer structured, stable wording so logs are easy to search.

## Level Usage
- `debug`: execution flow and diagnostics.
- `info`: major milestones and successful high-level operations.
- `warning`: recoverable issues or degraded behavior.
- `error`: failures that abort the current operation.

## Error Logging and Exceptions
- Services and clients should raise typed HAPE errors.
- Central error handling logs errors and prints user-facing messages.
- See `docs/dev/code-policy-error-handling.md` for the full error policy.
