# Stage 47 WSL Full-SAB Smoke Log

Date: 2026-06-26

## Goal

Refresh current-head complete SAB A/B smoke evidence on WSL/Linux after the
Stage 45 active-state refactor and Stage 46 target correctness smoke.

## Command

```text
STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage47_wsl_active_state_full_sab_smoke/r2 \
  STAGE20_ACTIVE_BENCH_RUNS=1 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 \
  bash scripts/run_stage20_active_buffer_bench.sh

STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage47_wsl_active_state_full_sab_smoke/r4 \
  STAGE20_ACTIVE_BENCH_RUNS=1 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 \
  bash scripts/run_stage20_active_buffer_bench.sh
```

Both runs used:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
KEY=BINARY
PARAM=SET_2_3_2048
```

## Result

| r | runs | reps | PVW us | repeated scalar us | speedup | status |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 1 | 1 | 13507287.000 | 16374054.000 | 1.212x | PASS |
| 4 | 1 | 1 | 24903657.000 | 33685084.000 | 1.353x | PASS |

Both process runs printed `SAB_PVW_BENCH correctness target_full ... Pass`.

## Scope

This stage is a current-head smoke after the active-state refactor. It confirms
that the promoted explicit path still has a positive complete-SAB A/B signal
on the selected WSL/Linux `spqlios_avx512` platform. It is not a replacement
for Stage 36 high-stat performance evidence and must not be used as a new
statistical performance claim.
