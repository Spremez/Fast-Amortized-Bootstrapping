# Stage 5 PVW Full Bootstrap Equivalence Log

Date: 2026-06-11

## Objective

Move `sab_pvw_*` from a test-only post-extract composition to a callable full
binary bootstrap API:

```text
sab_pvw_bootstrap_binary(...)
```

The new API performs:

```text
PVW setup/blind-rotate
-> PVW TLWE extraction
-> per-lane scalar TLWE materialization
-> existing full packing KS
-> existing HW-reducing KS
-> one final TRLWE output per lane
```

This is a correctness boundary, not a final performance claim. The blind
rotation/external-product part is PVW/MAT batched; the post-extract packing and
HW key switching are still scalar per lane.

## Code Artifacts

- `sab_pvw_new_binary_full_key(...)`
- `sab_pvw_bootstrap_binary(...)`
- `SAB_PVW_TARGET_TEST=true`

The original `sab_pvw_new_binary_key(...)`,
`sab_pvw_bootstrap_wo_extract_binary(...)`, and default scalar
`sab_rlwe_bootstrap(...)` paths remain available.

## Small Full-API Gate

Shape:

- `r = 1, 2, 4`
- `in_N = 16`
- `out_N = 1024`
- `h = 2`
- `r_prec = 3`
- binary deterministic sparse input gaps `{5, 4, 7}`
- full packing KS: `ell = 2`, `base_bit = 14`
- HW-reducing KS: `ell = 12`, `base_bit = 1`

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API full bootstrap binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

## Target-Shape Full-API Gate

Shape:

- `r = 2`
- `in_N = 2048`
- `out_N = 2048`
- `h = 39`
- `r_prec = 7`
- message precision: `3`
- binary deterministic sparse input gaps:
  - 8 gaps of 52
  - 31 gaps of 51
  - final gap 51
- output key: PVW ternary sparse, `h_out = 512`, sigma `2^-50`
- packing key: scalar ternary sparse, `h = 256`, sigma `2^-44`
- full packing KS: `ell = 2`, `base_bit = 14`
- HW-reducing KS: `ell = 12`, `base_bit = 1`

The target gate compares each PVW output lane against a repeated scalar
`sab_rlwe_bootstrap(...)` reference using the corresponding scalar lane key.

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
./main
```

Result:

```text
SAB_PVW target full bootstrap binary lane equivalence r=2 h=39 r_prec=7: Pass
SAB_PVW target full bootstrap gate: Pass
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
SAB_PVW API full bootstrap binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

FFNT is still a correctness/portability smoke only.

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
Bootstrapping time: 12,319,596 us +- 822,306.249888
Pass
```

The default scalar build still does not link `sab_pvw.o`.

## Remaining Boundary

This stage proves full-output correctness for one deterministic target-shape
gate. It does not prove final optimization success.

Next gates:

- Stage 6: multi-seed correctness and noise comparison.
- Stage 7: full SAB performance A/B with latency, per-lane throughput, key
  size, memory, and backend effects separated.
