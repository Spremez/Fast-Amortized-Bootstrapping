# Stage 5 PVW Extract Equivalence Log

Date: 2026-06-11

## Objective

Move the correctness boundary from PVW no-extract accumulators to extracted
PVW TLWE samples:

```text
PVW_TMLWE accumulator array -> PVW_TLWE extracted samples
```

The checked invariant is:

```text
phase(extract(pvw_acc[idx]).body[q])
==
phase(extract(scalar_acc[q][idx]))
```

for every accumulator index `idx` and lane `q`.

This gate is still before packing keyswitch, HW-reducing keyswitch, noise
evaluation, and full `sab_rlwe_bootstrap(...)` performance measurement.

## Implementation Notes

New API:

- `sab_pvw_extract_pvwtlwe(...)`

This stage also fixes `pvmtmlwe_extract_pvmtlwe_key(...)` so it writes into the
actual `PVW_TLWE_Key` layout `s[lane][index]`. The previous indexing wrote
`s[index][lane]`, which does not match `pvwtlwe_alloc_key(...)`.

## Test Shape

- `r = 1, 2, 4`
- `in_N = 16`
- `out_N = 1024`
- `h = 2`
- `r_prec = 3`
- deterministic binary sparse distances `{5, 4, 7}`
- one shared scalar input/control ciphertext
- `r` independent TV/body lanes

## WSL/Linux spqlios Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API extract binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API extract binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API extract binary lane equivalence r=4 h=2 r_prec=3: Pass
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
SAB_PVW API extract binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API extract binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API extract binary lane equivalence r=4 h=2 r_prec=3: Pass
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
Bootstrapping time: 14,243,122 us +- 137216.020510
Pass
```

The default scalar build still does not link `sab_pvw.o`.

## Remaining Boundary

The next correctness boundary is no longer raw extraction. It is:

```text
PVW_TLWE extracted lanes -> packing/HW KS comparable output
```

That requires deciding whether to add PVW-aware packing/HW key-switching or to
materialize per-lane scalar TLWE samples before reusing the existing scalar
packing/HW keys.
