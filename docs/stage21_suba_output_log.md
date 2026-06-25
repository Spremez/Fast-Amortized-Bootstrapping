# Stage 21 sub_a Output-Fusion Log

Date: 2026-06-25

## Goal

Test whether the inactive PVW active-buffer accumulator can be used as the
direct output of `sub_a` rotation, avoiding the internal `tmp -> active` copy
inside `sab_pvw_sub_a_binary`.

The change is gated by:

```text
SAB_PVW_ACTIVE_BUFFER_FUSION=true
SAB_PVW_SUBA_OUTPUT_FUSION=true
```

Default scalar SAB, default PVW SAB, and Stage 20 active-buffer behavior remain
unchanged unless the explicit flag is used.

## Algorithm Delta

Stage 20 carries a PVW active buffer through `RGSW_monomial_mul` and calls
`sub_a` in place on the active buffer. Stage 21 instead writes the rotated
state into the inactive buffer and flips active parity:

```text
active = RGSW_monomial_mul_state(buffers, active, selector)
sub_a_to(buffers[active ^ 1], buffers[active], a)
active = active ^ 1
```

For `BINARY SET_2_3_2048`:

```text
h = 39
r_prec = 7
RGSW monomial calls = 40
sub_a calls = 39
Stage 20 final copyback = 0
Stage 21 final copyback = 1
```

The extra final copyback is expected because the 39 `sub_a_to` steps flip the
active parity. The intended gain is removal of 39 full accumulator-array copies
inside `sub_a`.

## Correctness And Profile Gates

| gate | artifact | status |
|---|---|---|
| target full-output r=2 | `repro/stage21_suba_output_target_full.log` | PASS |
| default target regression | `repro/stage21_default_target_regression.log` | PASS |
| sub_a output profile r=2/r=4 | `repro/stage21_suba_output_profile_avx512_runs1/summary.csv` | PASS |
| unprofiled full SAB smoke r=2 | `repro/stage21_suba_output_bench_r2_reps1_runs1_seq/summary.csv` | PASS, not promoted |
| unprofiled full SAB smoke r=4 | `repro/stage21_suba_output_bench_r4_reps1_runs1_seq/summary.csv` | PASS, not promoted |

Profile command:

```bash
STAGE21_SUBA_PROFILE_RUNS=1 \
STAGE21_SUBA_PROFILE_R_VALUES="2 4" \
STAGE21_SUBA_PROFILE_OUT_DIR=repro/stage21_suba_output_profile_avx512_runs1 \
bash scripts/run_stage21_suba_output_profile.sh
```

Profile result:

| r | CMUX/MAT EP | NCMUX | sub_a | sub_a_to | copyback | expected copyback | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 573440 | 5080 | 39 | 39 | 1 | 1 | PASS |
| 4 | 573440 | 5080 | 39 | 39 | 1 | 1 | PASS |

The count gate confirms that Stage 21 changes only the `sub_a` output location
and active parity. The CMUX, NCMUX, MAT external-product, and sparse schedule
counts remain the same.

## Full SAB Smoke

Backend and shape:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
SAB_PVW_SUBA_OUTPUT_FUSION=true
KEY=BINARY
PARAM=SET_2_3_2048
```

Sequential one-process smokes, one timing rep per process:

| r | PVW us | scalar repeated us | speedup | Stage 20 mean | decision |
|---:|---:|---:|---:|---:|---|
| 2 | 16991710 | 19309859 | 1.136x | 1.270x | neutral/negative |
| 4 | 30760328 | 40232320 | 1.308x | 1.346x | neutral |

An earlier parallel r=2/r=4 smoke was discarded because both commands shared
`build/` and `main`, so the results were not valid evidence.

## Decision

Stage 21 supports:

```text
[implementation exists behind explicit flag]
[target correctness supported]
[profile count effect confirmed]
[sub_a output-to-inactive-buffer semantics validated]
```

Stage 21 does not support:

```text
[promotion over Stage 20]
[default enablement]
[full SAB speedup claim]
[noise/resource claim]
```

The candidate is a useful reference for later schedule-fusion work, but the
current full SAB evidence does not justify enabling it by default. Stage 20
`SAB_PVW_ACTIVE_BUFFER_FUSION=true` remains the current best explicit comparison
baseline.
