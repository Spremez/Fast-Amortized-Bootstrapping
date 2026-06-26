# Stage86 Secondary CMUX Materialization Plan

## Goal

Use Stage82 and Stage84 evidence to decide whether CMUX materialization is a
valid next implementation target, without repeating the Stage18/23
epilogue-only neutral ablations.

## Inputs

- `repro/stage82_post_h11_profile/profile_metrics.csv`
- `repro/stage84_h13_r6_tile_sweep_preflight/summary.csv`
- `docs/stage18_cmux_profile_and_fusion_log.md`
- `docs/stage23_schedule_fused_cmux_log.md`

## Command

```bash
python scripts/build_stage86_secondary_cmux_materialization.py
```

## Gates

| Gate | Pass condition |
|---|---|
| inputs | Stage82 profile exists and Stage84 decision is not-promoted |
| materiality | non-MAT share and from_DFT/add share remain large enough |
| prior-neutral guard | Stage18/23 neutral ablations are recorded |
| candidate screen | select a candidate distinct from wrapper epilogue fusion |
| security boundary | no key-format or selector-visibility change |
| decision | select a flagged backend materialization preflight only |

## Expected Output

- `docs/stage86_secondary_cmux_materialization_log.md`
- `repro/stage86_secondary_cmux_materialization/candidates.csv`
- `repro/stage86_secondary_cmux_materialization/decision.csv`
- `theory_checks/h14_secondary_cmux_materialization.md`
- `algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md`

## Promotion Policy

Stage86 itself does not promote code. A selected candidate must enter a later
implementation preflight with:

- explicit build flag;
- scalar/default path unchanged;
- identity-lane correctness;
- materialization microbench;
- same-backend complete SAB A/B;
- noise/resource gates if complete SAB is positive.
