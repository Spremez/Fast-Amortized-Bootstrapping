# Stage80 Promotion Integration Or Rejection Audit Plan

Date: 2026-06-26

## Goal

Turn the Stage79 r=6 fused-MAT review-required result into an explicit policy
decision before any later variant triage. Stage80 does not change scalar SAB,
does not change `sab_pvw_*` defaults, and does not upgrade the r=6 fused path
to a promoted default.

## Inputs

- Stage79 summary: `repro/stage79_rgt4_fused_high_stat/summary.csv`
- Stage79 full-SAB statistics:
  `repro/stage79_rgt4_fused_high_stat/full_sab_high_stat.csv`
- Stage79 noise/resource summaries:
  `repro/stage79_rgt4_fused_high_stat/noise_summary.csv`,
  `repro/stage79_rgt4_fused_high_stat/resource_summary.csv`
- Static implementation guards:
  - `src/mosfhet/Makefile.def`
  - `src/mosfhet/src/mattrgsw.c`
  - `scripts/run_stage79_rgt4_fused_high_stat.sh`

## Policy

The Stage79 r=6 fused result may be promoted only if it clearly beats the
Stage36 r=4 reference under the same backend while passing noise and resource
gates. Stage79 did not meet that boundary: r=6 mean speedup is `1.367x`, below
the Stage36 r=4 mean `1.377x`, despite passing noise/resource gates.

Therefore the Stage80 expected decision is:

```text
PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED
```

This means:

- keep `MAT_TRGSW_AVX512_RGT4_FUSED` available as an explicit experimental
  flag for future analysis;
- do not make it default;
- do not describe it as the promoted line;
- proceed to Stage81 variant triage from a clean policy state.

## Gates

| gate | pass condition |
|---|---|
| Stage79 precondition | Stage79 decision is `PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED` |
| performance policy | r=6 high-stat result is below automatic promotion boundary |
| noise/resource guard | Stage79 noise and resource rows pass |
| default-path guard | r>4 fused code remains behind `MAT_TRGSW_AVX512_RGT4_FUSED ?= false` |
| current-head smoke | scalar binary, explicit PVW target, and scalar ternary smoke pass |
| decision | keep experimental, not promoted |

## Repro Command

```bash
bash scripts/run_stage80_promotion_policy_audit.sh
```

## Outputs

- `repro/stage80_promotion_policy_audit/current_smoke/summary.csv`
- `repro/stage80_promotion_policy_audit/summary.csv`
- `docs/stage80_promotion_policy_audit_log.md`
