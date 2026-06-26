# Stage89 H14 Promotion Policy Integration Plan

Date: 2026-06-26

## Goal

Decide how the Stage88 H14-C1 backend FromDFT-add promotion candidate is
exposed after repeated complete-SAB, final-output noise, and resource gates.

The decision must not change scalar `sab_rlwe_bootstrap`, must not change
default `sab_pvw_*` behavior, and must keep backend/SIMD evidence separate
from paper-level novelty claims.

## Inputs

- Stage87 H14-C1 backend FromDFT-add preflight.
- Stage88 repeated/noise/resource gate for r=6.
- Stage80 promotion-policy precedent for H11 r=6 fused MAT.
- Stage36 r=4 high-stat complete-SAB reference.

## Commands

```bash
STAGE89_OUT_DIR=repro/stage89_h14_promotion_policy_integration \
FFT_LIB=spqlios_avx512 \
bash scripts/run_stage89_h14_promotion_policy_integration.sh
```

## Gates

| gate | requirement |
|---|---|
| Stage88 precondition | Stage88 decision is a recorded promotion candidate |
| current-head smoke | scalar binary full run, backend PVW target gate, scalar ternary build pass |
| default guard | `SAB_PVW_BACKEND_FROM_DFT_ADD` remains explicit and default false |
| policy comparison | H14 backend beats wrapper on repeated complete-SAB and is compared with Stage36/Stage80 precedent |
| claim guard | any promotion is explicit-path only, not default or paper-level novelty |

## Decision Labels

- `PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT`
- `PASS_STAGE89_H14_BACKEND_KEEP_EXPERIMENTAL_NOT_PROMOTED`
- `FAIL_STAGE89_H14_PROMOTION_POLICY`

## Failure Handling

If current-head smoke or default guards fail, do not promote or claim H14. If
the Stage88 performance evidence is positive but too weak for promotion, keep
the flag experimental and continue with profile/ablation only.
