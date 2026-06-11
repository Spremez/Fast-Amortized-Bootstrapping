# Stage 5 PVW Binary Sparse Mul Equivalence Log

Date: 2026-06-11

## Objective

Move the SAB-PVW lane invariant from full encrypted `RGSW_monomial_mul` to the
binary `sparse_mul` sequence used by the target `SET_2_3_2048` branch:

```text
RGSW_monomial_mul -> binary sub_a -> ... -> final RGSW_monomial_mul
```

The checked invariant is:

```text
phase(pvw_acc[idx].body[q] after sparse phase t)
==
phase(scalar_acc[q][idx] after the same scalar phase t)
```

for all accumulator indices `idx`, lanes `q`, and checked phases.

## Implementation Boundary

The executable test is compiled only with:

```text
SAB_PVW_KERNEL_TEST=true
```

This stage now uses the real `sab_pvw_*` API skeleton:

- `include/sab_pvw.h`
- `src/sab_pvw.c`
- `SAB_PVW_Key`
- `sab_pvw_RGSW_monomial_mul(...)`
- `sab_pvw_sub_a_binary(...)`
- `sab_pvw_sparse_mul_binary(...)`

The PVW selector schedule is materialized from a deterministic binary sparse
input key instead of hand-built MAT selector arrays in `main.c`.

The production scalar `sub_a(...)`, `sparse_mul(...)`, and
`sab_rlwe_bootstrap(...)` paths are not modified.

## Test Coverage

The API binary sparse test covers:

- `r = 1, 2, 4`
- `r_prec = 3`, with test accumulator count `in_N = 16`
- `h = 2`
- deterministic binary sparse distances `{5, 4, 7}` for
  `RGSW -> sub_a -> final RGSW`
- encrypted PVW and scalar accumulator inputs
- encrypted MAT_TRGSW and scalar TRGSW selector sets
- PVW and scalar automorphism key-switch in every NCMUX branch
- binary `sub_a` only:

```text
p[idx] <- X^{a[idx]} * p[idx]
```

The binary `sub_a` check compares after every intermediate phase:

1. after each `RGSW_monomial_mul`
2. after each binary `sub_a`
3. after the final `RGSW_monomial_mul`

Branches not covered here:

- ternary `sub_a`
- include-zero `sub_a`
- gaussian `sub_a_ga`
- target-size `h=39, in_N=2048`
- full `sab_pvw_*` bootstrapping with extraction/key-switch output

## WSL/Linux spqlios Correctness Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API binary sparse_mul lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API binary sparse_mul lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API binary sparse_mul lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
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
Bootstrapping time: 14,834,289 us +- 912289.559140
Pass
```

This confirms the production scalar path remains runnable after adding the
isolated binary sparse test.

## FFNT Portable Smoke

Command:

```bash
make clean
make FFT_LIB=ffnt SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API binary sparse_mul lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API binary sparse_mul lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API binary sparse_mul lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

FFNT is used here only as a correctness/portability smoke check.

## Stage 5 Handoff

The `sab_pvw_*` context/API skeleton now exists and the binary sparse gate uses
it. The next required step is full small-shape bootstrapping integration:

```text
PVW key/context -> MAT selector schedule -> PVW accumulator array ->
setup_tv_xb -> binary sparse_mul -> per-lane extraction/output comparison
```

Only after that full bootstrapping path passes correctness can performance,
noise, and throughput claims be evaluated.
