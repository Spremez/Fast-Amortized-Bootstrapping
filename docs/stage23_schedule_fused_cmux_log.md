# Stage 23 Schedule-Fused CMUX/NCMUX Log

Date: 2026-06-25

## Goal

Test whether the SAB RGSW monomial schedule can safely force the Stage 18
`from_DFT_add` CMUX epilogue inside the hot schedule and improve complete
PVW/MAT-SAB throughput.

The candidate is explicit:

```text
SAB_PVW_SCHEDULE_FUSED_CMUX=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
FFT_LIB=spqlios_avx512
```

It does not change scalar `sab_rlwe_bootstrap`, and it does not change public
`sab_pvw_CMUX` / `sab_pvw_NCMUX` semantics. The new wrappers are used only
inside `sab_pvw_RGSW_monomial_mul_state`.

## Static Model

For `BINARY SET_2_3_2048`:

```text
in_N = 2048
r_prec = 7
h + 1 = 40
CMUX/MAT EP calls = 40 * 7 * 2048 = 573440
NCMUX calls = 40 * (2^7 - 1) = 5080
schedule_fused_direct_CMUX calls = 573440 - 5080 = 568360
sub_a calls = 39
copyback calls = 0 with Stage 20 active-buffer fusion
```

## Gates

| gate | artifact | status |
|---|---|---|
| target full-output correctness with Stage 23 flag | `repro/stage23_schedule_fused_target_full.log` | PASS |
| default target regression without Stage 23 flag | `repro/stage23_default_target_regression.log` | PASS |
| r=2/r=4 schedule count profile | `repro/stage23_schedule_fused_profile_avx512_runs1/summary.csv` | PASS |
| r=4 full SAB 3-run sequential A/B | `repro/stage23_schedule_fused_bench_r4_reps1_runs3_seq/summary.csv` | PASS_NEUTRAL |
| r=2 full SAB 3-run sequential A/B | `repro/stage23_schedule_fused_bench_r2_reps1_runs3_seq/summary.csv` | PASS_NEUTRAL |

One initial r=2/r=4 benchmark attempt was launched in parallel and used the
same `build/` and `main` outputs. Those runs are recorded as invalid and are
not used for any claim:

```text
repro/stage23_schedule_fused_bench_r4_reps1_runs3/summary.csv
repro/stage23_schedule_fused_bench_r2_reps1_runs3/summary.csv
```

## Profile Result

The instrumented profile matched the schedule model for both r values.

| r | CMUX | NCMUX | schedule fused direct CMUX | schedule fused NCMUX | MAT EP | sub_a | copyback | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 573440 | 5080 | 568360 | 5080 | 573440 | 39 | 0 | PASS |
| 4 | 573440 | 5080 | 568360 | 5080 | 573440 | 39 | 0 | PASS |

The profile also shows `cmux_add_us=0` under this candidate because the add is
folded into `pvmtmlwe_from_DFT_add`. This is profile evidence only; it is not a
complete SAB latency claim.

## Full SAB Result

Valid runs are sequential process-level runs, one timing rep per process.

| r | runs | PVW mean us | PVW min | PVW max | scalar repeated mean us | mean speedup | min | max | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 3 | 15673397.333 | 15058181 | 16636523 | 19898011.667 | 1.273x | 1.153x | 1.343x | neutral |
| 4 | 3 | 29651483.333 | 29263194 | 30278977 | 39568238.333 | 1.335x | 1.304x | 1.377x | neutral |

Comparison against prior baselines:

| r | Stage 20 active-buffer mean speedup | Stage 22 specialized active-buffer mean speedup | Stage 23 mean speedup |
|---:|---:|---:|---:|
| 2 | 1.270x | not repeated in Stage 22 | 1.273x |
| 4 | 1.346x | 1.373x | 1.335x |

Stage 23 does not improve the r=4 full SAB mean over the current best
experimental path. The r=2 result is essentially tied with Stage 20 and has a
wide min/max spread.

## Decision

Stage 23 is correct and useful as an ablation, but it is not promoted.

Supported:

```text
[correctness supported] The schedule-local fused CMUX/NCMUX wrappers preserve
the tested binary target output and match exact call-count expectations.
```

Not supported:

```text
[performance not promoted] The candidate does not deliver a stable complete
SAB throughput improvement over the current active-buffer plus specialized
MAT-AVX512 path.
```

Next stage:

```text
Do not spend the next loop on this exact epilogue-only schedule fusion.
Move to Stage 24 conditional tail profiling, and then Stage 25 correctness,
noise, and resource validation for the current best explicit path unless the
tail profile reveals a material post-processing bottleneck.
```
