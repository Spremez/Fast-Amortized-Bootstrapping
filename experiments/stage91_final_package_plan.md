# Stage91 Final SAB Optimization Package Plan

Date: 2026-06-26

## Goal

Freeze the current scoped PVW/MAT-SAB engineering package after Stage90. This
stage is a final evidence and claim-boundary package, not a new hot-path
optimization and not a novelty/theorem-level paper claim.

## Scope

Stage91 records:

- the current supported PVW/MAT-SAB algorithmic path;
- complete-SAB throughput evidence for target binary `r=2/4`;
- the preferred explicit `r=6` H14 backend path and its evidence level;
- correctness/noise/resource support;
- negative and neutral ablations;
- exact claim levels and blocked claims after Stage90;
- reproduction commands and artifact pointers.

## Gates

- **Smoke/current-code gate**: Stage89 current-head smoke must pass, and no
  SAB source files may have changed after the Stage89 promotion-policy commit.
- **Performance gate**: Stage36 target binary high-stat performance must pass
  for `r=2/4`; Stage88 H14 `r=6` evidence may be reported only as a preferred
  explicit engineering path.
- **Noise/resource gate**: Stage36 target noise/resource and Stage88 H14
  noise/resource must pass under their recorded scopes.
- **External-claim gate**: Stage90 must keep native perf, full-text, and novelty
  blockers visible unless external evidence has actually been registered.
- **Closure/verifier gate**: Stage42, Stage51, Stage57, Stage59, and Stage68
  must be consistent after Stage91 is connected.

## Command

```bash
bash scripts/run_stage91_final_package.sh
```

## Expected Current Decision

```text
PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED
```

This means the scoped engineering acceleration package is final-package ready,
while stronger claims remain blocked.
