# Stage132 Lane-Pair CMUX Consumption Gate

Date: 2026-07-03

## Decision

`PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED`

Stage132 validates the first isolated CMUX-delta consumer boundary for
the Stage131 compact EP public API.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage132_mosfhet_static_build | PASS | make_static_spqlios_enable_pvw | true | MOSFHET static library builds with Stage131 compact EP API. |
| stage132_probe_compile | PASS | public_header_link | true | Standalone CMUX-consumption probe compiles against mosfhet.h. |
| stage132_probe_run | PASS | probe_returncode | 0 | Lane-pair CMUX delta consumption probe executed. |
| stage132_lane_pair_consumer_correctness | PASS | rows;max_component_gap;max_delta_gap;max_consumer_gap | 6;14689;14699;14699 | Per-lane delta and base-plus-delta phase/noise gates pass. |
| stage132_decision | PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED | promotion_policy |  | Stage132 opens a lane-state accumulator design, not full SAB speed claims. |

## API Rows

| r | N | seed | component mm | delta phase mm | consumer phase mm | noise mm | shared-output negative failures | max component gap | max delta gap | max consumer gap | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 512 | 0 | 0 | 0 | 0 | 0 | 16 | 14656 | 14644 | 14644 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 4 | 512 | 0 | 0 | 0 | 0 | 0 | 17 | 11345 | 11349 | 11349 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 6 | 512 | 0 | 0 | 0 | 0 | 0 | 28 | 13484 | 13478 | 13478 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 2 | 1024 | 0 | 0 | 0 | 0 | 0 | 129 | 12110 | 12113 | 12113 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 4 | 1024 | 0 | 0 | 0 | 0 | 0 | 458 | 14689 | 14699 | 14699 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |
| 6 | 1024 | 0 | 0 | 0 | 0 | 0 | 851 | 13183 | 13171 | 13171 | PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION |

## Interpretation

The lane-pair compact EP output can be consumed by a per-lane
`base + delta` accumulator update without phase/noise mismatch in this
deterministic gate. The negative control shows that replacing the
lane-pair masks by one shared output mask is invalid for r>1.
