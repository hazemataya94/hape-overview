# HAPE Testing Rules

Apply these rules when creating, updating, or running tests in this repository.

## Hard rules
- Hard rule: Prefer local functional tests and use `kind` for Kubernetes and EKS-like workflows.
- Hard rule: Do not create, update, or depend on real EKS clusters unless the user explicitly requests it.
- Hard rule: Default test flows must avoid billable cloud resources and external infrastructure dependencies.
- Hard rule: For cloud-related logic, use local validation plus mocks/stubs when behavior can be verified locally.
- Hard rule: For multi-node behavior, define node topology in versioned `kind` config and simulate EKS metadata with worker node labels.
- Hard rule: Functional test suites must be opt-in via environment flags and must default to cleanup after test completion.

## Validation requirements
- Validate output behavior, not only implementation details.
- Assert sorting and projection formulas for cost-report features.
- Verify missing request handling and default replica behavior.
- Keep tests deterministic, isolated, and repeatable on a developer laptop.

## Documentation requirements
- Keep a test README per functional suite with prerequisites, run commands, and cleanup behavior.
- State clearly that local tests do not require EKS unless explicitly requested.

## Mandatory self-check before final response
- Confirm the test approach uses local `kind` and does not require EKS by default.
- Confirm default test commands do not create billable cloud resources.
- Confirm the functional test README includes local run and cleanup instructions.
