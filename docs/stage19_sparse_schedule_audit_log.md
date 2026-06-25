# Stage 19 Sparse Schedule Audit Log

Date: 2026-06-25

## Goal

Confirm the exact sparse SAB schedule after the Stage 18 neutral
from-DFT-add result, and prepare the next active-buffer/copyback fusion step.

This stage is an instrumented profile gate. Its timing values are useful for
attribution, but they are not final latency claims.

## Implementation

Added per-bit counters under `SAB_PVW_BODY_PROFILE=true`:

```text
bit<i>_ncmux_calls
bit<i>_ncmux_us
bit<i>_direct_cmux_calls
bit<i>_direct_cmux_us
bit<i>_total_update_calls
```

These fields are appended to the existing `SAB_PVW_BODY_PROFILE sample` line.
Default builds and scalar SAB are unchanged.

Added:

```text
scripts/run_stage19_sparse_schedule_audit.sh
```

The script validates:

- target correctness;
- `rgsw_monomial_calls == sparse_mul_calls * (h + 1)`;
- `cmux_calls == mat_ep_calls == rgsw_monomial_calls * r_prec * in_N`;
- `ncmux_calls == rgsw_monomial_calls * (2^r_prec - 1)`;
- `sub_a_calls == sparse_mul_calls * h`;
- `copyback_calls == rgsw_monomial_calls` when `r_prec` is odd;
- per-bit NCMUX/direct-CMUX/total-update counts.

## Command

```bash
STAGE19_SPARSE_PROFILE_RUNS=1 \
STAGE19_SPARSE_PROFILE_R_VALUES="2 4" \
STAGE19_SPARSE_PROFILE_OUT_DIR=repro/stage19_sparse_schedule_avx512_runs1 \
bash scripts/run_stage19_sparse_schedule_audit.sh
```

Configuration:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_BENCH=true
SAB_PVW_BODY_PROFILE=true
KEY=BINARY
PARAM=SET_2_3_2048
```

## Count Results

| r | status | in_N | h | r_prec | RGSW calls | CMUX calls | NCMUX calls | MAT EP calls | sub_a | copyback |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | PASS | 2048 | 39 | 7 | 40 | 573440 | 5080 | 573440 | 39 | 40 |
| 4 | PASS | 2048 | 39 | 7 | 40 | 573440 | 5080 | 573440 | 39 | 40 |

The static model is confirmed:

```text
(h + 1) * r_prec * in_N = 40 * 7 * 2048 = 573440
(h + 1) * (2^r_prec - 1) = 40 * 127 = 5080
```

## Per-Bit Count Results

Each bit contributes exactly `81920` total updates:

```text
40 RGSW calls * 2048 accumulator slots = 81920
```

| bit | expected NCMUX | expected direct CMUX | expected total updates | status |
|---:|---:|---:|---:|---|
| 0 | 40 | 81880 | 81920 | PASS |
| 1 | 80 | 81840 | 81920 | PASS |
| 2 | 160 | 81760 | 81920 | PASS |
| 3 | 320 | 81600 | 81920 | PASS |
| 4 | 640 | 81280 | 81920 | PASS |
| 5 | 1280 | 80640 | 81920 | PASS |
| 6 | 2560 | 79360 | 81920 | PASS |

Both r=2 and r=4 match these per-bit counts.

## Instrumented Timing Snapshot

The script uses the last profile line in each run, which corresponds to the
timed benchmark sample.

| r | PVW us | scalar repeated us | smoke speedup | sub_a us | copyback us |
|---:|---:|---:|---:|---:|---:|
| 2 | 17237430 | 22473234 | 1.304x | 456307 | 433177 |
| 4 | 32819360 | 43960558 | 1.339x | 1539782 | 700653 |

Interpretation:

```text
The count model is exact. The profile confirms that there are 40 forced
copyback opportunities at the target r_prec=7 and 39 sub_a steps. This supports
Stage 20 active-buffer fusion as the next implementation target.
```

The one-run speedups are smoke-only because the profile build is instrumented
and not a repeated performance campaign.

## Decision

Stage 19 supports:

```text
[correctness supported: target full r=2/r=4 PASS]
[schedule model confirmed: all static counts match]
[next target identified: active-buffer/copyback fusion]
```

Stage 19 does not support:

```text
[new performance claim]
[default promotion]
[noise/security claim]
```

Next step:

```text
Stage 20 should implement an explicit active-buffer RGSW monomial/sparse_mul
path that carries the active ping-pong buffer across sparse steps and delays
copyback until an API or extract boundary.
```
