# Stage81 Next Variant Triage Plan

Date: 2026-06-26

## Goal

Select the next local PVW/MAT-SAB optimization direction after Stage80 keeps
H11 r=6 fused MAT as explicit experimental evidence only. Stage81 does not
modify SAB code and does not promote any path. It prevents blind implementation
work by requiring every next code variant to start from a falsifiable bottleneck
and a full gate plan.

## Inputs

- Stage69 feasibility audit: `repro/stage69_local_variant_feasibility.csv`
- Stage74 direct r>4 boundary: `repro/stage74_r_scaling_boundary/decision.csv`
- Stage75 r>4 profile boundary:
  `repro/stage75_rgt4_profile_boundary/profile_metrics.csv`
- Stage76 r>4 kernel feasibility:
  `repro/stage76_rgt4_kernel_feasibility/summary.csv`
- Stage79 high-stat fused result:
  `repro/stage79_rgt4_fused_high_stat/summary.csv`
- Stage80 policy decision:
  `repro/stage80_promotion_policy_audit/summary.csv`
- Stage24 post-processing tail:
  `repro/stage24_postproc_tail_avx512_runs1/summary.csv`

## Candidate Policy

- Do not continue direct r>4 lane scaling without a new layout or sparse-MAT
  hypothesis.
- Do not promote H11 r=6 fused MAT, because Stage80 explicitly keeps it
  experimental.
- Do not reopen post-processing unless a refreshed profile exceeds the Stage24
  tail threshold.
- Do not implement sparse selector shortcuts without a key-format and security
  argument.
- If local optimization continues, run a profile-only post-H11 fused r=6
  attribution gate before writing new hot-path code.

## Expected Decision

```text
PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION
```

This decision means the next local engineering action is measurement, not a
new algorithmic implementation: profile the explicit H11 fused r=6 path enough
to decide whether the next real target is MAT multiply/layout, CMUX/from-DFT
materialization, schedule/sub_a traffic, allocation, or tail processing.

## Repro Command

```bash
python scripts/build_stage81_next_variant_triage.py
```

## Outputs

- `repro/stage81_next_variant_triage.csv`
- `docs/stage81_next_variant_triage_log.md`
