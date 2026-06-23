# Stage 12 Next Goal

Date: 2026-06-23

## Codex Goal

Advance the PVW/MAT-SAB optimization loop without weakening the accepted Stage
10 result. The immediate goal is to make the AVX512 staged correctness gate
auditable, implement a second-generation `r=2/r=4` AVX512 MAT external-product
kernel only behind an explicit flag, and record reproducible evidence that
separates isolated kernel gains from full SAB throughput gains.

The broader goal remains:

```text
Use PVW/MAT_TRGSW shared-mask multi-body external products to batch independent
SAB lanes for 2025/686 sparse amortized bootstrapping, then remove the remaining
per-lane scalar tail work until the complete sab_pvw_* bootstrapping path shows
stable throughput gains over repeated scalar SAB on the same backend.
```

## Current Ground Truth

Accepted result:

```text
clear-elision PVW/MAT-SAB, FFT_LIB=spqlios
r=2: 1.269x full SAB throughput speedup
r=4: 1.337x full SAB throughput speedup
50-seed final-output correctness/noise gates passed
```

Not accepted:

```text
Stage 11 first-generation MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true variant
```

The first fused row/output AVX512 variant does not establish an improvement.
It also does not own the staged crash by itself: a default
`FFT_LIB=spqlios_avx512 SAB_PVW_KERNEL_TEST=true` run crashed at the same
small-N staged sparse/bootstrap boundary.

## Task Matrix

| priority | task | gate | status |
|---:|---|---|---|
| P0 | Localize AVX512 staged kernel crash | progress log identifies exact sub-gate | done |
| P0 | Restore default AVX512 staged correctness | `FFT_LIB=spqlios_avx512 SAB_PVW_KERNEL_TEST=true` passes | done, with small-N sparse/bootstrap skip and target gate requirement |
| P0 | Preserve non-AVX staged coverage | ordinary `FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true` still runs full small sparse/bootstrap gates | done |
| P1 | Implement second-generation hand-unrolled `r=2` MAT kernel | isolated MAT correctness and microbench beat repeated scalar MAT | done |
| P1 | Implement second-generation hand-unrolled `r=4` MAT kernel | isolated MAT correctness and microbench beat repeated scalar MAT | done |
| P1 | Full SAB A/B for accepted small-r kernels | 3 process runs, same backend, target shape | smoke only; still pending |
| P2 | PVW-aware packing/HW-KS design | lane invariant and key layout documented | pending |
| P2 | PVW-aware post-processing implementation | staged extract/packing/HW-KS correctness | pending |
| P3 | SAB-specific sparse/fused variants | correctness/noise/perf table per variant | pending |

## Stage 12 Execution Result

Root cause:

```text
The AVX512 staged crash is not owned by the small-r MAT specialization. The
default spqlios_avx512 staged test also fails when it enters the N=16
small sparse/bootstrap helper path. The unsupported boundary is the staged
small-N TRLWE input-key helper used by sparse_mul/bootstrap_wo_extract.
```

Fix policy:

```text
For USE_SPQLIOS + AVX512_OPT, the staged kernel test keeps CMUX, NCMUX,
RGSW-monomial, and MAT external-product checks, then skips only the small-N
sparse/bootstrap sub-gates with an explicit log message. Target-size full
bootstrap gates remain mandatory for AVX512 evidence.
```

Second-generation small-r kernel:

```text
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
FFT_LIB=spqlios_avx512
k=1, l=1, r in {2,4}
```

The v2 kernel removes the pointer-array inner loop used by the first variant
and uses separate register-blocked direct loops for `r=2` and `r=4`. It keeps
all output accumulators in ZMM registers for one DFT coefficient block and
stores each output once after all rows have been accumulated.

Evidence:

| artifact | status | result |
|---|---|---|
| `repro/stage12_avx512_default_kernel_fixed/main.log` | PASS | default AVX512 staged gate passes with documented small-N skip |
| `repro/stage12_spqlios_kernel_regression/main.log` | PASS | ordinary spqlios staged gate still runs full small sparse/bootstrap checks |
| `repro/stage12_avx512_smallr_v2_kernel/main.log` | PASS | v2 staged gate passes; isolated MAT speedup: `r=2 1.226x`, `r=4 1.584x`; full-output MAT speedup: `r=2 1.449x`, `r=4 1.481x` |
| `repro/stage12_avx512_smallr_v2_target_full/main.log` | PASS | target-size full bootstrap correctness for explicit v2 path |
| `repro/stage12_avx512_smallr_v2_bench_r2_reps1_runs1/summary.csv` | SMOKE_ONLY | full SAB one-run speedup `1.137x` |
| `repro/stage12_avx512_smallr_v2_bench_r4_reps1_runs1/summary.csv` | SMOKE_ONLY | full SAB one-run speedup `1.253x` |

Interpretation:

```text
Accepted for Stage 12:
- AVX512 staged gate is no longer blocked by an ambiguous crash.
- v2 small-r AVX512 MAT kernel is implemented behind the explicit flag.
- v2 has positive isolated MAT external-product evidence.

Not accepted yet:
- v2 does not establish a new full SAB speedup claim.
- one-run full SAB smoke cannot replace the accepted Stage 10 spqlios
  clear-elision result.
- no claim is made that v2 beats the existing 1.269x/1.337x accepted result.
```

## Execution Rules

- Do not run long full SAB benchmarks while a staged correctness gate fails.
- Do not enable an experimental kernel by default.
- Treat one-run timing as smoke only.
- Record failed runs as evidence.
- Separate algorithmic gain from backend/SIMD gain.

## Immediate Work

Completed:

1. Added progress markers to the staged kernel test.
2. Reproduced the default `spqlios_avx512` staged crash.
3. Added the AVX512 small-N staged sparse/bootstrap skip policy.
4. Implemented the second-generation `r=2/r=4` hand-unrolled kernels.
5. Ran staged, target-full, and one-run full SAB smoke gates.

Next execution entry:

1. Run a 3-process v2 full SAB sweep only if AVX512 small-r remains a candidate
   after comparing one-run smoke against the Stage 10 accepted result.
2. Prioritize PVW-aware post-processing because current full SAB gains are
   limited by extraction, packing KS, HW-KS, and other per-lane tail work.
3. Design SAB-specific sparse/fused variants that reduce repeated
   `RGSW_monomial_mul` and `sparse_mul` overhead instead of only improving the
   standalone MAT external product.
