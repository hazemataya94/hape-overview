# Error Handling Code Policy

## Purpose
Define one error handling approach for all HAPE commands and services.

## Core Rules
- Raise typed HAPE errors in services only.
- Clients should raise raw exceptions; services wrap them as typed HAPE errors.
- Do not raise raw `Exception` in domain logic.
- Do not catch and suppress errors inside services unless cleanup is required.
- Catch errors at the CLI boundary in one central place.
- Print short user-facing error messages.
- Log one error line for each failure.
- Do not include context-rich log payloads.
- Do not use retryable flags in error models.

## Error Types
- `HapeValidationError` for invalid input or missing required data.
- `HapeOperationError` for business/preflight flow failures.
- `HapeExternalError` for failures from external systems.
- `HapeUserAbortError` for user-initiated stop actions.

## Message Catalog
- Keep error text in `core/errors/messages/`.
- Split message files by domain such as `jira_error_messages.py`, `gitlab_error_messages.py`, and `jira_error_messages.py`.
- Use stable error codes such as `EKS_ROTATION_NO_ROLES`.

## HAPE Handler Contract
- Known HAPE errors: log one line, print mapped message, return mapped exit code.
- Unknown errors: log one line with class and message, print generic fallback message, return exit code `99`.

## Exit Codes
- `2` validation and input errors.
- `3` operation and external dependency errors.
- `130` user abort.
- `99` unknown error.
