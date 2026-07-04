# Stage317 Candidate: `ifft_batch5` Tile3+Tile2

## Summary

- Parent algorithm: PVW/MAT-SAB direct sub-DTF materialization.
- Focused module: SPQLIOS AVX512 inverse transform for gadget rows.
- Optimization target: isolated IFFT component time, then complete SAB `T_bootstrap/r`.
- Status labels: `[experimental gate]`, `[implementation pending]`, `[not a SAB claim]`.
- Main hypothesis: tile3+tile2 row batching can share trig-table loads enough
  to reduce the isolated IFFT component by at least 0.107769.

## Mathematical Definition

The transform result is unchanged:

```text
forall row in 0..4: out[row] = IFFT(row)
```

The variant changes only the backend schedule used to compute those five
independent row transforms.

## Pseudocode

```text
Input: tables, row0..row4
Output: row0..row4 after the same IFFT as five scalar calls
1. For trig-loading IFFT regions, process row0..row2 as one tile.
2. Process row3..row4 as the second tile.
3. For non-trig regions, preserve the same row-wise equations.
4. Return transformed rows.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| five `ifft(tables,row)` calls | one isolated `ifft_batch5_tile32` backend routine | implements same transform schedule with shared trig loads | Stage317 static gate only |

## Required Experiments

- Baseline: five existing AVX512 `ifft` calls.
- Metric: isolated IFFT time and exact row-wise output equivalence.
- Success: at least 0.107769 IFFT component reduction.
- Failure: any output mismatch, zmm/GPR spills that erase benefit, or reduction below gate.
