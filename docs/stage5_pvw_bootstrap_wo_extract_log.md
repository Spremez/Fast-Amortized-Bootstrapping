# Stage 5 PVW Bootstrap-Wo-Extract Equivalence Log

Date: 2026-06-11

## Objective

Move the `sab_pvw_*` correctness boundary from binary `sparse_mul` to the
small no-extract bootstrapping path:

```text
setup_tv_xb -> blind_rotate(binary sparse_mul) -> accumulator array
```

This is still not full `sab_rlwe_bootstrap(...)`: extraction, packing
keyswitch, HW-reducing keyswitch, noise studies, and target-size performance are
not covered by this gate.

## Implementation Boundary

New API functions:

- `sab_pvw_setup_tv_xb(...)`
- `sab_pvw_blind_rotate_binary(...)`
- `sab_pvw_bootstrap_wo_extract_binary(...)`

The scalar `sab_rlwe_bootstrap(...)` route is unchanged. The gated test compiles
only with:

```text
SAB_PVW_KERNEL_TEST=true
```

## Test Shape

- `r = 1, 2, 4`
- `in_N = 16`
- `out_N = 1024`
- `h = 2`
- `r_prec = 3`
- deterministic binary sparse distances `{5, 4, 7}`
- one shared scalar input/control ciphertext
- `r` independent TV/body lanes in one PVW accumulator

The scalar reference executes the same scalar hot-path sequence:

```text
scalar setup_tv_xb -> scalar RGSW_monomial_mul -> scalar binary sub_a -> final scalar RGSW_monomial_mul
```

It intentionally avoids constructing scalar packing/HW keys because those are
outside the no-extract boundary and previously triggered unrelated constructor
failure on this small artificial shape.

## WSL/Linux spqlios Gate

Command:

```bash
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
stdbuf -o0 ./main
```

Result:

```text
SAB_PVW API bootstrap_wo_extract binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API bootstrap_wo_extract binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API bootstrap_wo_extract binary lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

## FFNT Portable Smoke

Command:

```bash
make clean
make FFT_LIB=ffnt SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API bootstrap_wo_extract binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API bootstrap_wo_extract binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API bootstrap_wo_extract binary lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

## Scalar Baseline Smoke

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
Max monomial distance (log B): 7
Bootstrapping time: 14,148,310 us +- 343424.840034
Pass
```

The default build does not link `sab_pvw.o`.

## Next Gate

The next Stage 5 gate is target-shape or extraction-aware integration:

```text
bootstrap_wo_extract small gate -> target-shape wo_extract gate ->
per-lane extract -> packing/HW KS comparison -> full SAB A/B benchmark
```
