# Stage114 Lane-Local Resource Model

Date: 2026-07-03

## Decision

`PASS_STAGE114_RESOURCE_MODEL_NOT_FATAL_TOY_C_REQUIRED`

Stage114 screens the lane-local multimask candidate before C work. The
symbolic model says the accumulator grows, but the raw product-count
gain is not immediately erased. This is not measured performance.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage114_resource_rows | PASS | r_values | 2;4;6;8 | Resource model covers r=2,4,6,8. |
| stage114_accumulator_overhead | PASS_RECORDED | lane_local/current_acc_polys | 1.333;1.600;1.714;1.778 | Lane-local masks increase accumulator polynomial count. |
| stage114_coarse_tradeoff | PASS_NOT_FATAL | min_product_over_accumulator_ratio | 1.350 | Raw arithmetic gain remains above accumulator polynomial overhead in this symbolic model. |
| stage114_decision | PASS_STAGE114_RESOURCE_MODEL_NOT_FATAL_TOY_C_REQUIRED | next_gate_policy |  | Resource model does not immediately kill lane-local multimask, but implementation risk remains high. |

## Resource Model

| r | current acc polys | lane-local acc polys | acc ratio | dense products | lane products | product ratio | selector ratio | coarse ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 3 | 4 | 1.333 | 9 | 5 | 1.800 | 1.111 | 1.350 |
| 4 | 5 | 8 | 1.600 | 25 | 9 | 2.778 | 0.720 | 1.736 |
| 6 | 7 | 12 | 1.714 | 49 | 13 | 3.769 | 0.531 | 2.199 |
| 8 | 9 | 16 | 1.778 | 81 | 17 | 4.765 | 0.420 | 2.680 |