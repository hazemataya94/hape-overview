# Terraform Status

## Purpose
Track current Terraform scope for HAPE infrastructure.

## Current status
- `infrastructure/terraform/` is a placeholder.
- No Terraform modules or environments are defined yet.

## Planned direction
- Add reusable modules under `infrastructure/terraform/modules/`.
- Add environment stacks under `infrastructure/terraform/envs/` when infrastructure requirements are defined.
- Keep future module design aligned with least-privilege and secure defaults.

## Validation steps
- Confirm placeholder status:
  ```bash
  ls infrastructure/terraform
  ```
- Confirm no `.tf` files exist yet:
  ```bash
  rg --files infrastructure/terraform -g "*.tf"
  ```

## Related files
- `infrastructure/terraform/README.md`
- `infrastructure/README.md`
