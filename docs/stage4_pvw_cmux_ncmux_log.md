# Stage 4 PVW CMUX/NCMUX Equivalence Log

Date: 2026-06-11

## Objective

Validate the isolated SAB-PVW lane invariant before connecting any PVW code to
the production SAB bootstrapping path:

```text
phase(acc_pvw.body[q]) == phase(acc_scalar[q])
```

for `r=1/2/4`.

## Implementation Boundary

The executable test is compiled only with:

```text
SAB_PVW_KERNEL_TEST=true
```

The default scalar `sab_rlwe_bootstrap(...)` route is not modified.

Coverage:

- CMUX selector `0/1` on encrypted PVW samples copied to scalar lane samples.
- NCMUX selector `0/1` on trivial/noiseless inputs using the raw
  `X -> X^{-1}` polynomial automorphism before CMUX.

Known limitation:

- This does not solve full encrypted PVW NCMUX because
  `pvmtmlwe_keyswitch(...)` is still unimplemented. Stage 5 must decide whether
  to implement PVW automorphism/key-switch support or avoid that boundary by a
  different lane-state schedule.

Status update: Stage 5 implements PVW TMLWE automorphism/key-switch and verifies
full encrypted multibit `RGSW_monomial_mul` lane equivalence. This Stage 4 note
records the earlier boundary rather than the current project state.

## WSL/Linux spqlios Correctness Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW isolated CMUX/NCMUX lane equivalence r=1: Pass
SAB_PVW isolated CMUX/NCMUX lane equivalence r=2: Pass
SAB_PVW isolated CMUX/NCMUX lane equivalence r=4: Pass
MAT_TRGSW/PVW Stage 4 kernel test: Pass
```

Selected same-run MAT timings:

| r | MAT vs scalar speedup | MAT full vs scalar full speedup |
|---:|---:|---:|
| 1 | 1.035x | 0.907x |
| 2 | 1.216x | 1.234x |
| 4 | 1.024x | 1.111x |

These are not final performance claims. They are single-run smoke values from
the same binary used for the correctness gate.

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
Input: (N=2048, h=39, binary, sigma=2^-15)
Packing: (N=2048, h=256, ternary, sigma=2^-44)
Output: (N=2048, h=512, ternary, sigma=2^-50)
Message precision: 3 - Repetitions: 3
Bootstrapping time: 14,234,175 us +- 196,411.932021
Pass
```

This confirms the scalar baseline remains runnable after adding Stage 4 test
code.

## FFNT Portable Smoke

Command:

```bash
make clean
make FFT_LIB=ffnt SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW isolated CMUX/NCMUX lane equivalence r=1: Pass
SAB_PVW isolated CMUX/NCMUX lane equivalence r=2: Pass
SAB_PVW isolated CMUX/NCMUX lane equivalence r=4: Pass
MAT_TRGSW/PVW Stage 4 kernel test: Pass
```

FFNT results are recorded only as correctness/portability smoke, not as a
performance conclusion.

## Stage 5 Handoff

The next gate is isolated `RGSW_monomial_mul` lane equivalence:

```text
CMUX/NCMUX lane state -> RGSW monomial bit steps -> sparse_mul -> sab_pvw_*
```

The main unresolved design decision is the encrypted NCMUX automorphism
boundary. The existing PVW keyswitch stub must not be called from a production
path.

Status update: this design decision is resolved in Stage 5 for the isolated
RGSW monomial path. The next unresolved boundary is binary `sparse_mul`.
