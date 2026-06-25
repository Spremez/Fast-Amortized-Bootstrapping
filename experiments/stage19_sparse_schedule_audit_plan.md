# Stage 19 Sparse Schedule Audit Plan

Date: 2026-06-25

## Objective

Before implementing active-buffer or schedule fusion, verify the exact sparse
SAB schedule and attribute the remaining complete-SAB cost to actionable
components.

## Target Configuration

```text
KEY=BINARY
PARAM=SET_2_3_2048
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
r in {2,4}
```

## Expected Counts

For the target binary path:

```text
in_N = 2048
r_prec = 7
h + 1 = 40
cmux-class updates per RGSW monomial = 7 * 2048 = 14336
total cmux-class updates = 40 * 14336 = 573440
ncmux per RGSW monomial = 1 + 2 + 4 + 8 + 16 + 32 + 64 = 127
total ncmux = 40 * 127 = 5080
```

The audit must record whether `mat_ep_calls`, `cmux_calls`, and per-bit counts
match this model.

## Required Counters

Add or verify counters for:

- `setup_tv_xb_calls/us`;
- `blind_rotate_calls/us`;
- `sparse_mul_calls/us`;
- `rgsw_monomial_calls/us`;
- `cmux_calls/us`;
- `ncmux_calls/us`;
- `mat_ep_calls/us`;
- `cmux_sub_calls/us`;
- `cmux_from_dft_calls/us`;
- `cmux_add_calls/us`;
- `ncmux_auto_calls/us`;
- `sub_a_calls/us`;
- `copyback_calls/us`;
- per-bit CMUX/NCMUX counts for bit `0..6`.

## Correctness Gate

Each profiled run must print:

```text
SAB_PVW_BENCH correctness target_full Pass
```

If the profile build changes code generation or timing materially, it must be
labeled as instrumented and not used as final latency evidence.

## Decision Gate

Stage 19 produces one of these decisions:

| decision | condition | next stage |
|---|---|---|
| schedule model confirmed | counts match theory and timing identifies copy/schedule cost | Stage 20 active-buffer fusion |
| model mismatch | counts differ from theory | fix model or instrumentation before optimization |
| copy/sub_a not material | copyback/sub_a are too small after Stage 18 | Stage 22 MAT AVX512 audit |
| from_DFT/add still material | CMUX epilogue remains dominant | Stage 23 broader schedule fusion |

## Planned Output

- `docs/stage19_sparse_schedule_audit_log.md`;
- `repro/stage19_sparse_schedule_profile_*/summary.csv`;
- updated `hypotheses/hypothesis_register.yaml`;
- updated `repro/run_log.csv` and `repro/reproduction_checklist.md`.
