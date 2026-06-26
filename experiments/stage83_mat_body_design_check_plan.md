# Stage83 MAT Body Design Check Plan

Date: 2026-06-26

## Objective

Stage83 converts the Stage82 post-H11 fused r=6 profile into a concrete
route to the remaining SAB optimization work. It does not modify scalar SAB,
default `sab_pvw_*`, or hot-path code.

The stage answers three questions:

1. Does the current route from Stage82 to final SAB optimization exist?
2. Which MAT-body candidate is low-risk enough to test next?
3. Which candidates are blocked by security/key-format or external perf inputs?

## Inputs

- `repro/stage81_next_variant_triage.csv`
- `repro/stage82_post_h11_profile/decision.csv`
- `repro/stage82_post_h11_profile/profile_metrics.csv`
- `theory_checks/h11_rgt4_fused_mat_kernel.md`
- `theory_checks/h13_mat_body_reduction_design.md`
- `algorithm_variants/pvw_sab_h13_mat_body_design.md`

## Command

```bash
python scripts/build_stage83_mat_body_design_check.py
```

## Correctness Gate

No ciphertext code runs in Stage83. Correctness for this stage means the
selected future candidate has a complete correctness plan:

- isolated MAT/PVW identity-lane equivalence;
- target full-output SAB equivalence before any claim;
- scalar baseline regression if shared code is touched;
- multi-seed final-output noise/resource gates before promotion.

## Performance Gate

Stage83 is not a performance claim. It must:

- use Stage82 profile shares as attribution only;
- record Amdahl-style full-body bounds for MAT-body-only improvements;
- require non-instrumented complete-SAB A/B before any bootstrapping claim;
- separate kernel, body, full-SAB, and backend/SIMD evidence.

## Failure Handling

- If Stage81 or Stage82 inputs are missing, stop and rerun those stages.
- If MAT EP is not the primary single component, reroute to schedule or
  materialization review rather than writing MAT kernel code.
- If the selected candidate requires key-format or selector-security changes,
  block implementation until a separate security design exists.
- If only native counters can decide the candidate, mark it external-blocked
  rather than inferring hardware behavior from WSL timing alone.

## Expected Output

- `repro/stage83_mat_body_design_check/candidates.csv`
- `repro/stage83_mat_body_design_check/decision.csv`
- `docs/stage83_mat_body_design_check_log.md`
