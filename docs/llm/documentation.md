# HAPE Documentation Rules

Apply these rules when creating or updating documentation in this repository.

## Documentation updates
- Update relevant documentation for every implemented change.
- Use simple, clear words and short sentences; avoid ambiguous words (`it`, `this`, `that`, `soon`, `latest`, `correct`).
- Write explicit statements with subject, condition, and expected result; prefer simple words (`fix` over `resolve`, `use` over `utilize`).
- For documents under `docs/ops/`, add a Mermaid flowchart when it helps provide a clear general workflow overview.

## Command examples in docs
- When writing documentation command examples for Python, always use `python` (never virtualenv-prefixed interpreter paths or `python3`).
- Keep commands copy-paste ready from repository root unless a different working directory is required.
