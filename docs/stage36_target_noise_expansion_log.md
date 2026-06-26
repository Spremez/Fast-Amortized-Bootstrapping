# Stage 36 Target-Noise Expansion Log

Date: 2026-06-26

## Purpose

This log records the Stage 36 target final-output noise rerun for the promoted
PVW/MAT-SAB path. It uses the target binary parameter `SET_2_3_2048`, r=2/r=4,
`spqlios_avx512`, specialized MAT-AVX512, and active-buffer fusion.

This is a statistical evidence refresh only. It does not change scalar SAB or
`sab_pvw_*` code and does not upgrade novelty, theorem-level citation,
non-binary, all-parameter, or hardware-counter claims.

## Command

```bash
STAGE36_MODE=target_noise \
STAGE36_EXECUTE=1 \
STAGE36_TARGET_NOISE_SEEDS=50 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
bash scripts/run_stage36_high_stat_expansion.sh
```

## Result

| r | seeds | points | pvw failures | scalar failures | pair failures | min pvw-scalar log2 | max pvw-scalar log2 | avg pvw-scalar log2 | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 50 | 204800 | 0 | 0 | 0 | -0.446 | 0.619 | -0.007400 | PASS |
| 4 | 50 | 409600 | 0 | 0 | 0 | -0.555 | 0.682 | -0.029200 | PASS |

## Interpretation

The refreshed target final-output noise campaign passed for both promoted
target r values. This strengthens target-noise statistical wording in the
scoped engineering package, but it does not affect the remaining external
blockers for native perf-counter attribution or 2025/686 full-text review.
