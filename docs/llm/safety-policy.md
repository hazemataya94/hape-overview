# HAPE Agent Policy
These rules define safety and scope for any LLM agent working in this repository.

## Default mode
- Default mode is **read + plan**.
- Prefer small diffs. Validate each change before adding more.

## Allowed actions
- Read repo files needed for the task.
- Propose and implement code + doc changes inside the repo.
- Run local checks (formatting, unit tests) when available.

## Disallowed actions
- Do not access or modify real infrastructure (Kubernetes clusters, AWS accounts, GitLab/Jira/Confluence orgs) unless the user explicitly requests it and provides the required access.
- Do not introduce new network calls to third-party services for “rendering” or “conversion” (example: diagram renderers). Prefer local tooling.
- Do not log secrets or write secrets into files. Never print tokens.

## Approval gates (when interacting with real systems)
- Anything that mutates external systems (create/update/delete, apply, deploy, rotate) needs an explicit user instruction.
- For risky operations, produce:
  - plan (steps)
  - blast radius
  - rollback
  - required inputs

## Output expectations
- Be explicit: state assumptions, inputs, and expected results.
- If a requirement is ambiguous, stop and ask one clarifying question.
- Never use real user device paths in documentation or defaults. Always use placeholders such as `/path/to/...`.
