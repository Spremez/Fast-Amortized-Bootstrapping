# Stage 48 WSL Final-Output Noise Smoke Log

Date: 2026-06-26

## Goal

Refresh current-head final-output noise and correctness smoke evidence on
WSL/Linux after the Stage 45 active-state refactor, Stage 46 target correctness
smoke, and Stage 47 complete-SAB A/B smoke.

## Command

```text
STAGE25_FINAL_NOISE_OUT_DIR=repro/stage48_wsl_active_state_noise_smoke \
  STAGE25_FINAL_NOISE_R_VALUES='2 4' \
  STAGE25_FINAL_NOISE_SEED_COUNT=1 \
  STAGE25_FINAL_NOISE_START_SEED=6862025 \
  SAB_PVW_NOISE_TRIALS=1 \
  FFT_LIB=spqlios_avx512 \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  bash scripts/run_stage25_final_noise_sweep.sh
```

## Result

| r | seeds | points | PVW failures | scalar failures | pair failures | PVW-scalar log2 gap | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1 | 4096 | 0 | 0 | 0 | 0.603 | PASS |
| 4 | 1 | 8192 | 0 | 0 | 0 | -0.555 | PASS |

Both raw logs printed `SAB_PVW_NOISE target full bootstrap gate: Pass`.

## Scope

This stage is a current-head smoke after the active-state refactor. It confirms
that the promoted explicit path still has final-output correctness/noise
continuity on the selected WSL/Linux `spqlios_avx512` platform. It is not a
replacement for Stage 36 high-stat target-noise evidence and must not be used
as a new statistical noise claim.
