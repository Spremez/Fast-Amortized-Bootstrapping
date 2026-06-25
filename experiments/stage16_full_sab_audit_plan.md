# Stage 16 Full SAB AVX512 Audit Plan

Date: 2026-06-25

## Objective

Promote or reject the Stage 15 AVX512 MAT external-product variant at the
complete SAB bootstrapping level.

## Primary Endpoint

Mean complete SAB throughput speedup over repeated scalar SAB:

```text
speedup = scalar_repeated_avg_us / pvw_avg_us
```

The endpoint is measured by the existing paired `SAB_PVW_BENCH` harness under:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
KEY=BINARY
PARAM=SET_2_3_2048
r in {2,4}
```

## Baselines

- repeated scalar `sab_rlwe_bootstrap` in the same binary and backend;
- accepted Stage 10 clear-elision `spqlios` result as cross-backend historical
  context only, not as the same-backend comparator.

## Gates

Correctness:

- every run must pass `SAB_PVW_BENCH correctness target_full`;
- all logs must be preserved.

Performance:

- default audit uses three process runs per r;
- every run must have speedup > 1.0x;
- mean speedup must be >= 1.10x to keep the variant promotable;
- r=2 and r=4 are judged independently.

Statistics:

- report mean/min/max speedup;
- report mean PVW latency and mean scalar repeated latency;
- label the result `[statistically supported engineering claim]` only after
  repeated runs pass; otherwise use `[performance smoke only]`.

Failure Handling:

- correctness failure: stop and mark Stage 16 failed;
- speedup instability: keep the path explicit-flag only;
- r-specific failure: allow a narrower r-specific promotion boundary.

## Repro Command

```bash
STAGE16_FULL_SAB_RUNS=3 STAGE16_FULL_SAB_REPS=1 \
STAGE16_FULL_SAB_OUT_DIR=repro/stage16_avx512_full_sab_audit_runs3_reps1 \
bash scripts/run_stage16_full_sab_audit.sh
```

## Expected Output

- `summary.csv`: one row per r with aggregated process-run results;
- `r2/summary.csv`, `r4/summary.csv`: raw per-process benchmark summaries;
- `r2/run_*.log`, `r4/run_*.log`: raw benchmark logs.
