# Stage 27 Final Full-SAB Performance Log

Date: 2026-06-25

## Goal

Re-run the current promoted explicit PVW/MAT-SAB path after the Stage 26
parameterized harness refactor, so final reports do not rely only on older
pre-Stage-26 timing records.

## Configuration

```text
FFT_LIB=spqlios_avx512
KEY=BINARY
PARAM=SET_2_3_2048
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
SAB_PVW_BENCH_REPS=1
STAGE20_ACTIVE_BENCH_RUNS=3
```

The comparison is complete `sab_pvw_*` target bootstrapping against repeated
scalar SAB under the same binary parameter set and backend.

## Results

| r | runs | correctness | PVW mean us | scalar repeated mean us | mean speedup | min speedup | max speedup | decision |
|---:|---:|---|---:|---:|---:|---:|---:|---|
| 2 | 3 | Pass | `14909221.667` | `17401413.000` | `1.171x` | `1.111x` | `1.285x` | positive but noisy |
| 4 | 3 | Pass | `26125921.000` | `36552608.667` | `1.401x` | `1.331x` | `1.472x` | strongest current target evidence |

Raw summaries:

- `repro/stage27_final_full_sab_active_r2_runs3/summary.csv`
- `repro/stage27_final_full_sab_active_r4_runs3/summary.csv`

## Interpretation

The current promoted path remains positive at the complete-SAB level after the
Stage 26 parameterized harness refactor. r=4 is the stronger and more stable
target evidence in this rerun. r=2 remains positive but has higher run-to-run
variance than earlier Stage 20 evidence, so final claims should report the
range rather than only the mean.

This performance rerun does not by itself promote any novelty claim, non-binary
claim, or broad all-parameter claim. It should be combined with Stage 25 noise
and resource records for the final engineering claim.

