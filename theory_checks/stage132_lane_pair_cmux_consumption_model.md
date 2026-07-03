# Stage132 Lane-Pair CMUX Consumption Model

Date: 2026-07-03

The Stage131 API produces `MAT_TRGSW_COMPACT_OUTPUT_DFT`, containing
one DFT mask/body pair per lane. Stage132 tests the narrow consumer
identity needed by CMUX:

```text
phase_q(base_q + delta_q) = phase_q(base_q) + phase_q(delta_q)
delta_q = compact_EP_q(in2 - in1)
```

This is a lane-state invariant. It does not prove that the output can
be represented as a standard `PVW_TMLWE_DFT` with one shared output
mask. The required negative control intentionally collapses all lane
masks to lane 0 and verifies that this produces phase failures.

## Results

| r | N | seed | component mm | delta phase mm | consumer phase mm | noise mm | shared-output negative failures | max component gap | max delta gap | max consumer gap | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 512 | 0 | 0 | 0 | 0 | 0 | 16 | 14656 | 14644 | 14644 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 4 | 512 | 0 | 0 | 0 | 0 | 0 | 17 | 11345 | 11349 | 11349 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 6 | 512 | 0 | 0 | 0 | 0 | 0 | 28 | 13484 | 13478 | 13478 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 2 | 1024 | 0 | 0 | 0 | 0 | 0 | 129 | 12110 | 12113 | 12113 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 4 | 1024 | 0 | 0 | 0 | 0 | 0 | 458 | 14689 | 14699 | 14699 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 6 | 1024 | 0 | 0 | 0 | 0 | 0 | 851 | 13183 | 13171 | 13171 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |

## Boundary

Passing this gate opens compact lane-state design for RGSW monomial
and sparse schedule integration. It is not complete SAB, not
multi-seed correctness/noise evidence, and not a `T_bootstrap/r`
performance claim.
