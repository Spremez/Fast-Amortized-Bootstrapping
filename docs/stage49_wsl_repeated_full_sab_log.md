# Stage 49 WSL Repeated Full-SAB Current-Head Stability Log

Date: 2026-06-26

## Goal

Strengthen the post-refactor current-head complete-SAB A/B evidence from the
Stage 47 single-run smoke to a repeated stability check on WSL/Linux.

## Command

```text
STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage49_wsl_repeated_full_sab/r2 \
  STAGE20_ACTIVE_BENCH_RUNS=3 \
  SAB_PVW_BENCH_R=2 \
  SAB_PVW_BENCH_REPS=1 \
  bash scripts/run_stage20_active_buffer_bench.sh

STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage49_wsl_repeated_full_sab/r4 \
  STAGE20_ACTIVE_BENCH_RUNS=3 \
  SAB_PVW_BENCH_R=4 \
  SAB_PVW_BENCH_REPS=1 \
  bash scripts/run_stage20_active_buffer_bench.sh
```

Both runs used the script defaults:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
KEY=BINARY
PARAM=SET_2_3_2048
```

## Result

| r | runs | reps | mean PVW us | mean repeated scalar us | mean speedup | speedup range | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 3 | 1 | 13757392.667 | 17395742.000 | 1.265x | 1.174x-1.338x | PASS |
| 4 | 3 | 1 | 24628013.000 | 33876383.333 | 1.376x | 1.356x-1.396x | PASS |

All six process runs printed `SAB_PVW_BENCH correctness target_full ... Pass`.

## Scope

This stage is current-head repeated stability evidence after the active-state
refactor. It is stronger than the Stage 47 one-run smoke but remains smaller
than the Stage 36 high-stat target-performance campaign. It should support
current-head continuity, not replace the Stage 36 performance claim source.
