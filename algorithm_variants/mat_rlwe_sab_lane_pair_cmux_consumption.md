# V132: Lane-Pair CMUX Delta Consumption

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: first SAB-facing consumer of compact EP output.
- Optimization target: complete-SAB amortized `T_bootstrap/r`.
- Status labels: `[isolated-consumer]`, `[lane-state-required]`,
  `[not-full-sab]`.
- Decision: `PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED`.

## Delta From Stage131

Stage131 validates the public external-product API. Stage132 adds the
next invariant: converting each lane-pair DFT output to torus and
adding it to an accumulator base preserves the expected per-lane
phase/noise. It deliberately keeps the output as lane-pair state.
