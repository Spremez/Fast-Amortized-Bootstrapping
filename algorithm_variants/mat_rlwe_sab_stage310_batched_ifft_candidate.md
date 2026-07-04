# Stage310 Batched IFFT Candidate Card

## Summary

- Parent algorithm: PVW/MAT-SAB direct sub-DTF materialization path.
- Focused module: SPQLIOS reverse FFT after digit-to-double materialization.
- Optimization target: lower `T_bootstrap/r` by reducing direct DFT lifecycle time.
- Status labels: `[experimental gate]`, `[backend ABI required]`.
- Main hypothesis: a true batched IFFT backend could improve the Stage307 IFFT
  residual because multiple rows share FFT tables and schedule structure.

## Mathematical Definition

The ciphertext algebra is unchanged. A batch IFFT candidate would replace
independent maps `IFFT(row_i)` for `i in 0..r` with a backend routine
`BatchIFFT(row_0, ..., row_r)` that returns exactly the same DFT-domain rows.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| per-row `ifft(tables, row)` | backend `BatchIFFT(tables, rows)` | implements same transform | Stage310 admits only if backend proof exists |

## Complexity Change

- Time: asymptotically still `(k+r) * IFFT(N)`; possible constant-factor gain only.
- Memory: no key-format change expected; temporary row pointers or backend scratch may grow.
- What must be measured: isolated FFT correctness, per-row IFFT time, complete SAB `T_bootstrap/r`.

## Theory Dependencies

- Inherited assumptions: all external-product algebra and gadget decomposition remain unchanged.
- Proof steps affected: none if each row output is bitwise/numerically equivalent within existing tolerance.
- New lemmas needed: equivalence of backend batch transform to independent row transforms.
- Current status: `PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED`.

## Required Experiments

- Baselines: current direct DFT path and scalar repeated SAB.
- Metrics: IFFT per-row microbench, direct lifecycle profile, full SAB `T_bootstrap/r`.
- Success criteria: isolated IFFT correctness; component reduction; full SAB speedup with no correctness/noise regression.
- Failure criteria: wrapper-only implementation, no component reduction, or full SAB neutral result.
