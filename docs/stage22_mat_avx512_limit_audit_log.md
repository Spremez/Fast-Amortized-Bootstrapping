# Stage 22 MAT-Aware AVX512 Limit Audit Log

Date: 2026-06-25

## Goal

Audit whether the current MAT-aware AVX512 external-product implementation is
near the useful practical limit for the tested PVW/MAT-SAB target, and whether
additional r-specific AVX512 work should remain a priority.

The comparison is same-backend:

```text
generic:     FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=false
specialized: FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
```

The complete SAB comparison uses the current best explicit body path:

```text
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

## Gates

| gate | artifact | status |
|---|---|---|
| generic staged MAT/PVW kernel | `repro/stage22_mat_avx512_limit_audit_runs1_full1/generic/kernel_run_0.log` | PASS |
| specialized staged MAT/PVW kernel | `repro/stage22_mat_avx512_limit_audit_runs1_full1/specialized/kernel_run_0.log` | PASS |
| r=2/r=4 full SAB smoke | `repro/stage22_mat_avx512_limit_audit_runs1_full1/full_sab_smoke.csv` | PASS |
| r=4 full SAB 3-run comparison | `repro/stage22_mat_avx512_full_r4_runs3/full_sab_smoke.csv` | PASS |
| objdump instruction count | `repro/stage22_mat_avx512_full_r4_runs3/instruction_counts.csv` | PASS, proxy only |

Hardware perf counters were not used for the Stage 22 conclusion. The
instruction evidence is an objdump proxy, not a cycles/load/store counter
claim.

## Initial r=2/r=4 Smoke

One process run per variant:

| r | generic PVW us | specialized PVW us | specialized/generic PVW | generic full-SAB speedup | specialized full-SAB speedup |
|---:|---:|---:|---:|---:|---:|
| 2 | 17865224 | 16558623 | 1.079x | 1.111x | 1.140x |
| 4 | 31236042 | 28851014 | 1.083x | 1.295x | 1.369x |

This was used only to decide whether a repeated r=4 comparison was worth
running.

## r=4 Repeated Full SAB Comparison

Three process runs, one timing rep per process:

| variant | runs | PVW mean us | PVW min | PVW max | scalar repeated mean us | mean speedup | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| generic MAT-AVX | 3 | 30005420.000 | 29197610 | 30483500 | 39579966.333 | 1.320x | 1.291x | 1.362x |
| specialized MAT-AVX | 3 | 28852643.333 | 28193894 | 29236920 | 39593140.667 | 1.373x | 1.313x | 1.437x |

Same-backend interpretation:

```text
specialized_vs_generic_pvw_speedup = 30005420.000 / 28852643.333 = 1.040x
```

The specialized MAT path gives a stable but modest r=4 full-SAB improvement
over the generic MAT path. This supports keeping
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true` for the optimized experimental path.

## Kernel Microbench And Phase Interpretation

The repeated r=4 audit run's staged kernel microbench shows:

| scope | r | generic MAT us | specialized MAT us | specialized/generic |
|---|---:|---:|---:|---:|
| DFT output | 2 | 14.018 | 9.441 | 1.485x |
| DFT output | 4 | 31.426 | 21.235 | 1.480x |
| full output | 2 | 23.363 | 16.868 | 1.385x |
| full output | 4 | 47.587 | 40.433 | 1.177x |

The r=4 full-output improvement is much smaller than the DFT-output improvement
because the dense MAT arithmetic and output conversion costs remain material.

Phase profile confirms the dense-MAT boundary:

| variant | r | scalar phase sum | MAT phase sum | scalar mul | MAT mul |
|---|---:|---:|---:|---:|---:|
| generic | 4 | 29.851 | 24.838 | 9.328 | 11.963 |
| specialized | 4 | 31.150 | 26.521 | 9.431 | 12.896 |

The MAT path saves decomposition and DFT work, but the `r=4` MAT multiply phase
is still larger than repeated scalar because dense MAT performs `25` complex
products versus the scalar repeated `16`.

## Instruction Audit

Objdump count over `mattrgsw.o + polynomial.o`:

| variant | vfmadd | vfnmadd | vfmsub | zmm refs | vmovapd | vmovupd |
|---|---:|---:|---:|---:|---:|---:|
| generic | 28 | 0 | 24 | 245 | 136 | 64 |
| specialized | 114 | 26 | 32 | 484 | 239 | 64 |

The specialized build clearly emits more direct AVX512 FMA-family instructions
in the MAT external-product object path. This supports an implementation-level
SIMD distinction, but it does not prove optimal load/store behavior without
hardware counters.

## Decision

Stage 22 supports:

```text
[same-backend specialized MAT-AVX512 benefit at complete SAB level]
[r=4 repeated full-SAB positive: specialized/generic PVW 1.040x]
[current specialized kernel meets the practical dense-MAT expectation]
```

Stage 22 does not support:

```text
[theoretical-optimal AVX512 claim]
[multi-fold acceleration from MAT kernel tuning alone]
[additional r=4 register-pressure-heavy unrolling as the next priority]
```

The next optimization priority should be Stage 23 schedule-level fusion or
Stage 25 noise/resource validation for the current promoted experimental path,
not another blind r=4 MAT pointer/register tiling attempt. Prior Stage 15
already rejected a more aggressive r=4 pointer-array variant because of
register/stack pressure; Stage 22 does not overturn that result.
