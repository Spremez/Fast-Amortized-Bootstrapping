# mat_rlwe_sab_stage331_current_head_highstat

## Summary

- Parent algorithm: PVW/MAT-RLWE multi-body path for 2025/686 SAB.
- Focused module: current-head complete SAB direct-DFT implementation.
- Optimization target: complete `T_bootstrap/r`.
- Status: `PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH`.

## Result

Current-head selected direct PVW/MAT-SAB:

- samples: `10`;
- mean `T_bootstrap/r`: `6117083.425` us;
- repeated scalar mean per lane: `10690503.200` us;
- speedup: `1.747647x`;
- noise pair failures: `0/10`.

## Paper Boundary

This variant supports a scoped systems claim only when the decision is
`PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH`.  It does not support theoretical
optimality or compact selector claims.
