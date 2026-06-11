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

Three correctness gates are checked:

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

3. `r_prec=3`, selector bits `{1,0,1}` with encrypted selectors and encrypted
   accumulator inputs
   - validates PVW automorphism/key-switch for the NCMUX branch;
   - uses scalar `trlwe_eval_automorphism(...)` as the oracle for every lane;
   - verifies full encrypted multibit `RGSW_monomial_mul` lane equivalence.

## PVW Automorphism Key-Switch

This stage adds PVW TMLWE key-switch support:

```text
pvmtmlwe_new_KS_key(...)
pvmtmlwe_new_automorphism_KS_key(...)
pvmtmlwe_keyswitch(...)
free_pvmtmlwe_ks_key(...)
```

The key-switch follows the scalar `trlwe_keyswitch(...)` pattern: decompose
each input mask polynomial, multiply the decomposition by a PVW_TMLWE_DFT
key-switch sample, accumulate in DFT form, transform back to torus form, and
subtract from the trivial sample carrying the input bodies.

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
SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=1 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=2 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=2 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=4 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=4 r_prec=3: Pass
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
SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=1 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=2 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=2 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=2 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit0 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence encrypted-selector bit1 r=4 r_prec=1: Pass
SAB_PVW isolated RGSW_monomial lane equivalence trivial-selector multibit r=4 r_prec=3: Pass
SAB_PVW isolated RGSW_monomial lane equivalence full-encrypted multibit r=4 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

FFNT is used here only as a correctness/portability smoke check.

## Current Limitation

This stage now proves full encrypted multibit `RGSW_monomial_mul` equivalence
for the isolated test shape. It still does not connect that implementation to
the production `sparse_mul(...)` or `sab_rlwe_bootstrap(...)` path.

The next missing piece is the `sparse_mul` boundary:

```text
RGSW_monomial_mul -> sub_a -> final RGSW_monomial_mul
```

The `sub_a` step has binary, ternary, include-zero, and gaussian branches. The
first PVW integration target should remain the binary branch used by
`SET_2_3_2048`; other branches need separate equivalence gates.

## Stage 5 Handoff

The isolated binary `sparse_mul` gate has passed and the first `sab_pvw_*`
context/API skeleton now owns the PVW side of that check. See
`docs/stage5_pvw_sparse_mul_log.md`.

The next gate was small no-extract bootstrapping correctness, starting with PVW
`setup_tv_xb`/blind-rotate output comparison before extraction and packing KS.
That gate now passes for `r=1/2/4`; see
`docs/stage5_pvw_bootstrap_wo_extract_log.md`.
