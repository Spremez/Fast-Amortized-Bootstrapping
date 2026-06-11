# Stage 5 PVW Packing/HW-KS Equivalence Log

Date: 2026-06-11

## Objective

Move the Stage 5 correctness boundary past extraction and through the existing
scalar post-processing path:

```text
PVW_TMLWE accumulator array
-> PVW_TLWE extracted samples
-> per-lane scalar TLWE materialization
-> full packing KS
-> HW-reducing TRLWE KS
```

This is still a transitional correctness gate. It does not yet implement a
PVW-native packing/HW-KS path and it does not claim full SAB bootstrapping
speedup.

## Checked Invariants

For every accumulator index `idx` and lane `q`:

```text
phase(materialize_lane(extract(pvw_acc[idx]), q))
==
phase(extract(scalar_acc[q][idx]))
```

After full packing KS:

```text
phase(pack(materialized_pvw_lane[q]))
==
phase(pack(scalar_extracted_lane[q]))
```

After HW-reducing KS:

```text
phase(hwks(pack(materialized_pvw_lane[q])))
==
phase(hwks(pack(scalar_extracted_lane[q])))
```

All checks compare decoded phases at the test message precision.

## Implementation Notes

Added gated test helpers in `main.c`:

- `copy_pvwtlwe_lane_to_tlwe(...)`
- `compare_tlwe_scalar_array_phases(...)`
- `compare_trlwe_pair_phases(...)`

The gate uses the same small binary SAB skeleton as the previous extract gate:

- `r = 1, 2, 4`
- `in_N = 16`
- `out_N = 1024`
- `h = 2`
- `r_prec = 3`
- deterministic binary sparse distances `{5, 4, 7}`

For post-extract key switching, the gate uses the target-style decomposition
shape:

- full packing KS: `ell_packing = 2`, `b_packing = 14`
- HW-reducing KS: `ell_hw = 12`, `b_hw = 1`

During bring-up, a temporary low-precision setting
`ell_packing=2,b_packing=4,ell_hw=2,b_hw=4` failed after extraction because the
additional keyswitch approximation/noise could move already-correct 3-bit
phases across a decode boundary. This failure mode confirms that post-extract
checks must use target-grade KS decomposition parameters.

## PVW TLWE Shared-Mask Safety Fix

This stage also fixes `PVW_TLWE` arithmetic helpers in
`src/mosfhet/src/pvwtlwe.c`.

`PVW_TLWE.a` is a shared mask of length `n`, while `PVW_TLWE.b` has `r` body
lanes. The old `pvwtlwe_copy/add/sub/scale/...` helpers iterated over `n*r`
mask coefficients and could write past the allocated shared mask. They now
iterate over `n` mask coefficients and `r` body coefficients.

## WSL/Linux spqlios Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API materialized TLWE binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API packing/HW-KS binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API materialized TLWE binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API packing/HW-KS binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API materialized TLWE binary lane equivalence r=4 h=2 r_prec=3: Pass
SAB_PVW API packing/HW-KS binary lane equivalence r=4 h=2 r_prec=3: Pass
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
SAB_PVW API materialized TLWE binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API packing/HW-KS binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API materialized TLWE binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API packing/HW-KS binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API materialized TLWE binary lane equivalence r=4 h=2 r_prec=3: Pass
SAB_PVW API packing/HW-KS binary lane equivalence r=4 h=2 r_prec=3: Pass
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
Bootstrapping time: 12,211,858 us +- 347,735.665185
Pass
```

The default scalar build still does not link `sab_pvw.o`.

## Remaining Boundary

Update: the next boundary has been checked for a callable full-output API and
one deterministic target-shape gate. See
`docs/stage5_pvw_full_bootstrap_log.md`.

The remaining boundary is now Stage 6/7 evidence:

```text
multi-seed correctness/noise
and full bootstrapping performance A/B
```

Only after those gates should this work claim final SAB bootstrapping speedup.
