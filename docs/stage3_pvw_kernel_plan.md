# Stage 3 PVW/Matrix Kernel Plan

Date: 2026-06-08

This document defines the next implementation target: an independent MOSFHET
matrix/PVW external-product kernel that can later be called by `sab_pvw_*`.

## Current Repository State

Existing structures in `src/mosfhet/include/mosfhet.h`:

- `PVW_TLWE`: LWE with one shared mask `a` and `r` bodies `b`.
- `PVW_TMLWE`: ring sample with `k` mask polynomials and `r` body polynomials.
- `PVW_TMLWE_DFT`: DFT form of `PVW_TMLWE`.
- `MAT_TRGSW` / `MAT_TRGSW_DFT` / `MAT_TRGSW_Key`: declared but not implemented.

Existing code in `src/mosfhet/src/pvwtmlwe.c`:

- Allocators for `PVW_TMLWE` and `PVW_TMLWE_DFT`.
- PVW TMLWE key generation, sample encryption, phase, add/sub/copy.
- `pvmtmlwe_decompose(...)`, which decomposes `k` masks and `r` bodies into
  `(k+r)*l` torus-polynomial rows.
- No implemented `MAT_TRGSW` allocation, encryption, DFT conversion, or matrix
  external product.

Risk in existing PVW TLWE code:

- `PVW_TLWE` allocates `a` with length `n`, but functions such as
  `pvwtlwe_copy`, `pvwtlwe_add`, `pvwtlwe_sub`, and scaling variants loop over
  `n*r` mask entries. This is not safe to reuse directly for hot paths.

## ENABLE_PVW_TMLWE Build Status

Command tested:

```bash
make -B FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false \
  PARAM=SET_2_3_2048 ENABLE_PVW_TMLWE=true \
  SAB_PROFILE=false SAB_MICROBENCH=false
```

Initial result: compile reached link stage, then failed.

Observed blockers:

- `pvmtmlwe_mv_extract_pvmtlwe` calls `pvmtlwe_negate(...)`, but the available
  function is `pvwtlwe_negate(...)`.
- `pvmtmlwe_eval_automorphism` calls missing `pvmtmlwe_keyswitch(...)`.

Interpretation:

- The PVW TMLWE source is not a reliable default dependency yet.
- Stage 3 should either fix only the minimal link blockers or add the new matrix
  kernel in a separate file gated by a new build switch.
- No SAB code should depend on the old PVW automorphism or keyswitch path until
  those functions have dedicated tests.

Follow-up fix:

- `pvmtmlwe_mv_extract_pvmtlwe` now calls `pvwtlwe_negate(...)`.
- A `pvmtmlwe_keyswitch(...)` aborting stub was added so the object links
  without pretending that the missing keyswitch is implemented.

Current result:

```text
ENABLE_PVW_TMLWE=true links successfully.
pvmtmlwe_keyswitch is still not implemented and aborts if called.
```

## mbfhe-mb Reference Semantics

The relevant reference path is:

- `D:\projects\mbfhe-mb\src\libtfhe\tgsw-fft-operations.cpp`
- `matrixTGswFFTExternMulToTLwe(...)`

Semantics:

```text
input accum has:
  k mask polynomials
  r body polynomials

decompose rows:
  mask rows: i in [0, k), level in [0, l)
  body rows: q in [0, r), level in [0, l)
  total rows = (k + r) * l

output:
  PVW TLWE/TMLWE FFT sample with the same k masks and r bodies
```

This differs from scalar TRGSW only in replacing `(k+1)*l` rows with
`(k+r)*l` rows and replacing one body with `r` bodies.

Important caveat:

`mbfhe-mb` has allocation/destructor quirks around `k+r` samples. We should not
copy that memory model directly. Use MOSFHET allocation/free conventions.

## Minimal Stage 3 API

Add MOSFHET-native functions, preferably in `pvwtmlwe.c` or a separate
`mattrgsw.c`:

```c
MAT_TRGSW_Key mat_trgsw_new_key(PVW_TMLWE_Key trlwe_key, int l, int Bg_bit);

MAT_TRGSW mat_trgsw_alloc_new_sample(int l, int Bg_bit, int k, int r, int N);
MAT_TRGSW_DFT mat_trgsw_alloc_new_DFT_sample(int l, int Bg_bit, int k, int r, int N);

void free_mat_trgsw(void * p);
void free_mat_trgsw_DFT(void * p);
void free_mat_trgsw_key(MAT_TRGSW_Key key);

void mat_trgsw_monomial_sample(MAT_TRGSW out, int64_t m, int e, MAT_TRGSW_Key key);
void mat_trgsw_to_DFT(MAT_TRGSW_DFT out, MAT_TRGSW in);
void mat_trgsw_monomial_DFT_sample(MAT_TRGSW_DFT out, int64_t m, int e, MAT_TRGSW_Key key);
```

Hot-path external product should avoid dynamic allocation:

```c
typedef struct _MAT_TRGSW_MUL_SCRATCH {
  TorusPolynomial * dec;
  DFT_Polynomial * dec_dft;
  int rows;
} * MAT_TRGSW_MUL_SCRATCH;

MAT_TRGSW_MUL_SCRATCH mat_trgsw_alloc_mul_scratch(int rows, int N);
void free_mat_trgsw_mul_scratch(MAT_TRGSW_MUL_SCRATCH scratch);

void mat_trgsw_mul_pvmtmlwe_DFT(
    PVW_TMLWE_DFT out,
    PVW_TMLWE in,
    MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch);
```

## External Product Algorithm

For `in` with `(k, r, N)`, selector with `(l, Bg_bit)`:

```text
rows = (k + r) * l

pvmtmlwe_decompose(scratch->dec, in, Bg_bit, l)
for p in [0, rows):
  torus_to_DFT(scratch->dec_dft[p], scratch->dec[p])

clear out
for p in [0, rows):
  for j in [0, k):
    out.a[j] += scratch->dec_dft[p] * selector.samples[p].a[j]
  for q in [0, r):
    out.b[q] += scratch->dec_dft[p] * selector.samples[p].b[q]
```

For `r=1`, this should match scalar TRGSW external product modulo the different
sample type and key layout.

## Tests Needed Before SAB Integration

Minimum tests before touching SAB:

- `ENABLE_PVW_TMLWE=true` links successfully.
- `r=1`: matrix external product agrees with scalar `trgsw_mul_trlwe_DFT` on
  decrypted phase for a monomial selector.
- `r=2` and `r=4`: each body decrypts to the scalar reference for the
  corresponding lane.
- Repeat microbench with no allocation in `mat_trgsw_mul_pvmtmlwe_DFT`.

Only after these pass should Stage 5 add `sab_pvw_*`.
