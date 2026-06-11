# Stage 5 PVW RGSW Monomial Equivalence Log

Date: 2026-06-11

## Objective

Move the SAB-PVW lane invariant from isolated CMUX/NCMUX to the
`RGSW_monomial_mul` bit-step scheduler:

```text
phase(pvw_acc[idx].body[q] after bit step t)
==
phase(scalar_acc[q][idx] after the same scalar bit step t)
```

for all accumulator indices `idx`, lanes `q`, and checked bit steps.

## Implementation Boundary

The executable test is still compiled only with:

```text
SAB_PVW_KERNEL_TEST=true
```

The production scalar `RGSW_monomial_mul(...)`, `sparse_mul(...)`, and
`sab_rlwe_bootstrap(...)` paths are not modified.

## Test Coverage

The Stage 5 isolated test covers `r=1/2/4` and uses the same PVW lane state as
Stage 4.

Two correctness gates are checked:

1. `r_prec=1`, encrypted selector bit `0` and `1`
   - validates the RGSW array scheduler with real encrypted scalar TRGSW and
     MAT_TRGSW selectors;
   - uses trivial/noiseless accumulator inputs so the NCMUX raw automorphism
     branch remains decryptable without PVW keyswitch.

2. `r_prec=3`, selector bits `{1,0,1}` with noiseless/trivial selectors
   - validates multi-bit buffer ping-pong, wraparound NCMUX positions, and
     non-wrap CMUX positions across several RGSW bit steps;
   - intentionally keeps selectors trivial so every intermediate state remains
     a valid trivial accumulator under the raw automorphism test model.

## WSL/Linux spqlios Correctness Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=1 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=1 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=1 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=2 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=4 r_prec=3: Pass
```

## Default Scalar SAB Smoke

Command:

```bash
make clean
make FFT_LIB=spqlios KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
Sparse bootstrapping with binary keys
Message precision: 3 - Repetitions: 3
Pass
```

This confirms the production scalar path remains runnable after adding the
isolated Stage 5 tests.

## FFNT Portable Smoke

Command:

```bash
make clean
make FFT_LIB=ffnt SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=1 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=1 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=1 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=2 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=4 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

FFNT is used here only as a correctness/portability smoke check.

## Current Limitation

This stage proves the PVW lane-state scheduler and MAT selector layout for
RGSW monomial bit steps, but it does not yet prove full encrypted multi-bit
`RGSW_monomial_mul` equivalence.

The missing piece is still the encrypted NCMUX automorphism boundary:

```text
pvmtmlwe_eval_automorphism -> pvmtmlwe_keyswitch(...)
```

`pvmtmlwe_keyswitch(...)` is currently an aborting stub, so the production PVW
path must not call it. The next engineering decision is whether to implement
PVW automorphism keyswitch or restructure the PVW SAB lane schedule so this
operation is avoided or delayed.

## Stage 5 Handoff

The next required gate before `sparse_mul` is one of:

1. implement and test PVW automorphism/key-switch for encrypted NCMUX; or
2. design an equivalent lane-state schedule that does not require
   `pvmtmlwe_keyswitch(...)` in the RGSW hot path.

Only after that can Stage 5 claim full encrypted `RGSW_monomial_mul`
equivalence and move to `sparse_mul`.
