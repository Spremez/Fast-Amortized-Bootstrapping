# V129: Compact EP Isolated Microbench

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: isolated compact EP all-lane timing.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[microbench]`, `[production-dft-linked]`, `[not-production-header]`, `[not-hot-path]`.
- Decision: `NEUTRAL_STAGE129_COMPACT_EP_MICROBENCH_NOT_PROMOTED`.

## Interpretation Rules

- Promote only toward production API design if r=4/r=6 compact all-lane
  timing beats the dense-count proxy.
- If only addmul wins but full timing loses, the next hypothesis must target
  decomposition/DFT reuse or streaming.
- If full timing wins, Stage130 may design a production-header API gate, still
  without changing scalar/default SAB.
