# Stage 45 Active-State Refactor Log

Date: 2026-06-26

## Goal

Make the Stage 20 active-buffer/copyback fusion state explicit in the
`sab_pvw_*` implementation without changing the scalar SAB path, the public
PVW API, or any performance claim.

## Code Delta

`src/sab_pvw.c` now uses an internal `SAB_PVW_Accumulator_State` for the
PVW accumulator ping-pong state:

```text
buffers[2]
active
in_N
lanes
r_prec
```

The public `sab_pvw_RGSW_monomial_mul()` wrapper still normalizes back to the
caller-visible accumulator before returning. The active-buffer sparse path
continues to carry the active buffer across RGSW monomial and `sub_a` steps,
then normalizes only at the sparse path boundary.

This is a maintainability and future-fusion change. It does not enable the
experimental path by default and does not alter scalar `sab_rlwe_bootstrap`.

## Verification

Portable correctness/build gate:

```text
make FFT_LIB=ffnt ARCH_FLAGS= SAB_PVW_KERNEL_TEST=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true KEY=BINARY PARAM=SET_2_3 -j2
./main
```

Result:

| check | status | artifact |
|---|---|---|
| r=1 sparse/full bootstrap lane equivalence | PASS | `repro/stage45_active_state_refactor/ffnt_kernel_run.log` |
| r=2 sparse/full bootstrap lane equivalence | PASS | `repro/stage45_active_state_refactor/ffnt_kernel_run.log` |
| r=4 sparse/full bootstrap lane equivalence | PASS | `repro/stage45_active_state_refactor/ffnt_kernel_run.log` |
| staged MAT/PVW kernel gate | PASS | `repro/stage45_active_state_refactor/ffnt_kernel_run.log` |

Platform check:

```text
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_TARGET_TEST=true \
  KEY=BINARY PARAM=SET_2_3_2048 -j2
```

On the current Windows/MSYS toolchain this remains blocked by the assembler
error `invalid register for .seh_savexmm`. This is a platform/build limitation,
not SAB algorithm evidence. Target-shape AVX512 correctness and performance
claims still require the WSL/Linux performance platform.

## Decision

The explicit active-state refactor is accepted as a correctness-preserving
maintenance step for the promoted explicit PVW/MAT-SAB path. It does not
upgrade the final goal beyond:

```text
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```
