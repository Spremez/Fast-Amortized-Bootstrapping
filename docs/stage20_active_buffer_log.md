# Stage 20 Active-Buffer Fusion Log

Date: 2026-06-25

## Goal

Use the Stage 19 exact schedule result to remove forced PVW accumulator
copyback after every RGSW monomial in the SAB sparse path.

The change is gated by:

```text
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

Default scalar SAB and default PVW SAB remain unchanged.

## Algorithm Delta

The original PVW RGSW monomial path starts from `p0`, runs the `r_prec`
ping-pong butterfly, and copies the active buffer back to `p0` whenever the
final active buffer is the scratch array.

For the target parameter:

```text
r_prec = 7
h = 39
RGSW monomial calls = h + 1 = 40
legacy copybacks = 40
```

Stage 20 adds an internal state path:

```text
active = sab_pvw_RGSW_monomial_mul_state(buffers, active, selector, sab)
sub_a(buffers[active], a)
```

The active buffer is carried across sparse steps. Normalization happens only
when the final active buffer differs from the public output buffer. For
`h + 1 = 40` and odd `r_prec = 7`, the final active buffer returns to the
original output, so the expected active-buffer copyback count is `0`.

## Correctness Gates

| gate | artifact | status |
|---|---|---|
| active-buffer target full-output | `repro/stage20_active_buffer_target_full.log` | PASS |
| default non-active target regression | `repro/stage20_default_target_regression.log` | PASS |
| active-buffer profile r=2/r=4 | `repro/stage20_active_buffer_profile_avx512_runs1/summary.csv` | PASS |
| active-buffer full SAB r=2 three-run | `repro/stage20_active_buffer_bench_r2_reps1_runs3/summary.csv` | PASS |
| active-buffer full SAB r=4 three-run | `repro/stage20_active_buffer_bench_r4_reps1_runs3/summary.csv` | PASS |

## Profile Gate

Command:

```bash
STAGE20_ACTIVE_PROFILE_RUNS=1 \
STAGE20_ACTIVE_PROFILE_R_VALUES="2 4" \
STAGE20_ACTIVE_PROFILE_OUT_DIR=repro/stage20_active_buffer_profile_avx512_runs1 \
bash scripts/run_stage20_active_buffer_profile.sh
```

Result:

| r | CMUX/MAT EP | NCMUX | sub_a | legacy copyback | active copyback | saved |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 573440 | 5080 | 39 | 40 | 0 | 40 |
| 4 | 573440 | 5080 | 39 | 40 | 0 | 40 |

The count gate confirms the intended schedule effect. The MAT external-product
count is unchanged, as expected.

## Full SAB A/B

Backend and shape:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
KEY=BINARY
PARAM=SET_2_3_2048
```

Three-process sweeps, one timing rep per process:

| r | runs | PVW mean us | scalar repeated mean us | mean speedup | min | max | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 3 | 16358590.667 | 20747480.333 | 1.270x | 1.173x | 1.349x | PASS |
| 4 | 3 | 31093757.667 | 41812418.333 | 1.346x | 1.323x | 1.384x | PASS |

Comparison to prior AVX512 full-SAB evidence:

| r | Stage 16 mean | Stage 18 fused mean | Stage 20 active-buffer mean |
|---:|---:|---:|---:|
| 2 | 1.197x | no repeated promotion | 1.270x |
| 4 | 1.281x | 1.285x | 1.346x |

Interpretation:

```text
The active-buffer path is the first post-Stage-18 candidate with repeated
complete-SAB improvement over the Stage 16/18 AVX512 MAT baseline. The r=4
result is the stronger signal. r=2 is positive on average but has wider run
spread and should remain scoped until further sweeps/noise/resource gates.
```

## Decision

Stage 20 supports:

```text
[implementation exists]
[correctness supported for target full-output]
[profile count effect confirmed: copyback 40 -> 0]
[repeated complete-SAB performance positive for r=2/r=4]
```

Stage 20 does not yet support:

```text
[default enablement]
[noise/resource claim]
[parameter-general claim]
[paper-ready claim]
```

Next step:

```text
Use SAB_PVW_ACTIVE_BUFFER_FUSION=true as the next explicit comparison baseline.
Proceed to Stage 25 correctness/noise/resource gates before default promotion,
or continue Stage 21 sub_a/rotation only if profile shows it remains material.
```
