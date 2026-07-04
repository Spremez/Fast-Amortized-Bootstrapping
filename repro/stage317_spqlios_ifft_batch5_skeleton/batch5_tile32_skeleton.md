# Batch5 Tile3+Tile2 Skeleton

This is a register-level skeleton, not an implemented backend symbol.

```text
ifft_batch5_tile32(tables, row0, row1, row2, row3, row4):
  for each IFFT loop region that loads trig tables:
    for each butterfly/vector position:
      load shared trig vectors once for tile rows 0..2
      apply the single-row butterfly equations to row0, row1, row2
      load shared trig vectors once for tile rows 3..4
      apply the same equations to row3, row4
  for size4/size2 regions with no trig-table sharing:
      either keep row-tiled form or fall back to per-row code
```

Register budget:

- full five-row offloop: 42 zmm registers, rejected;
- tile3 offloop: 26 zmm registers, admitted;
- tile2 offloop: 18 zmm registers, admitted.

Promotion requirement for Stage318: row-wise equivalence against five existing
`ifft` calls and at least 0.107769 isolated IFFT component reduction.
