
# HAPE Architecture Rules
Keep HAPE features aligned with the architecture and avoid layer leakage.

# Required architecture workflow
1. For HAPE feature work, read `docs/architecture.md` first.
2. Identify impacted layers before coding.
3. Implement all relevant layers for production-ready feature changes.

# Reuse before create
- Before creating new modules, check whether existing modules can be extended cleanly.
- Create new components only when extension would hurt cohesion or maintainability.

# Guardrails
- Do not move business logic into commands.
- Do not put third-party API logic into services when a client layer exists.
- Clients must not call other clients.
- Ask clarifying questions when requirements are ambiguous.
