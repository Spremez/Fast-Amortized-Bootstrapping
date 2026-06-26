# Stage82 Post-H11 Fused R6 Profile Plan

Date: 2026-06-26

## Goal

Run the profile-only attribution required by Stage81 before any new local
SAB/MAT hot-path implementation. This stage profiles the explicit H11
`MAT_TRGSW_AVX512_RGT4_FUSED` r=6 path under the same target binary setup and
records which component still dominates.

Stage82 does not promote H11, does not change defaults, and does not make
profile timing a final latency claim.

## Inputs

- Stage81 decision: `repro/stage81_next_variant_triage.csv`
- Stage75 generic r=6/r=8 profile boundary:
  `repro/stage75_rgt4_profile_boundary/profile_metrics.csv`
- Stage79 high-stat H11 r=6 result:
  `repro/stage79_rgt4_fused_high_stat/summary.csv`
- Stage80 H11 policy:
  `repro/stage80_promotion_policy_audit/summary.csv`
- Existing body-profile runner:
  `scripts/run_stage20_active_buffer_profile.sh`

## Repro Command

```bash
bash scripts/run_stage82_post_h11_profile.sh
```

## Gates

| gate | pass condition |
|---|---|
| inputs | Stage81/75/79/80 inputs exist and have expected decisions |
| profile run | r=6 fused body-profile run passes target correctness |
| schedule counts | CMUX/MAT EP `573440`, NCMUX `5080`, sub_a `39`, copyback `0` |
| attribution | component shares are recorded and labeled profile-only |
| decision | select a next measurement/design direction, not a promoted code path |

## Outputs

- `repro/stage82_post_h11_profile/stage82_run.log`
- `repro/stage82_post_h11_profile/body_profile_fused_r6/summary.csv`
- `repro/stage82_post_h11_profile/profile_metrics.csv`
- `repro/stage82_post_h11_profile/decision.csv`
- `docs/stage82_post_h11_profile_log.md`
