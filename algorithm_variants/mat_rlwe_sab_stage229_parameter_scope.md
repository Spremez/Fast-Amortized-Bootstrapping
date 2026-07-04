# Stage229 MAT-RLWE SAB Parameter Scope

## Supported Variant

The supported implementation object is the exact dense MAT/PVW-SAB path:

- shared mask;
- `r` body lanes;
- dense row-output MAT external product;
- scalar SAB default path preserved;
- explicit PVW/MAT flags required for optimized paths.

## Supported Claims

- Binary `SET_2_3_2048` r=2/r=4 has current-head complete-SAB A/B evidence.
- Binary `SET_2_3_2048` r=6 has current explicit exact-route evidence.
- Binary `SET_4_5_2048` and `SET_2_3_4096` have historical high-stat support.

## Unsupported Claims

- Ternary/include-zero PVW-SAB.
- All-parameter PVW/MAT-SAB generalization.
- Theoretical optimality of the current dense MAT external product.
- Paper novelty without source-verified related-work audit.
