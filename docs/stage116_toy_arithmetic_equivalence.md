# Stage116 Toy Arithmetic Equivalence

Date: 2026-07-03

## Decision

`PASS_STAGE116_TOY_ARITH_EQUIV_SELECTOR_PROTOTYPE_REQUIRED`

Stage116 compiles and runs a generated C arithmetic probe. It compares
dense shared-mask reference phases, lane-local compact phases, and the
known-bad current-format drop-offlane negative control.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage116_compile | PASS | gcc_compile | true | Generated toy arithmetic C probe compiled under WSL gcc. |
| stage116_dense_vs_lane_local | PASS | dense_lane_mismatches | 0;0;0;0;0;0 | Lane-local compact arithmetic matches dense reference for all tested coefficients. |
| stage116_negative_control | PASS_REJECTED_CURRENT_FORMAT | drop_failures | 128;512;253;1009;384;1529 | Current-format drop-offlane negative control fails as expected. |
| stage116_product_model | PASS | min_dense_over_lane_terms | 1.800000 | Dense product terms remain above lane-local terms for all toy cases. |
| stage116_decision | PASS_STAGE116_TOY_ARITH_EQUIV_SELECTOR_PROTOTYPE_REQUIRED | next_gate_policy |  | Toy arithmetic equivalence is finite evidence for opening a selector-format prototype only. |

## Equivalence Rows

| r | N | dense terms | lane terms | ratio | mismatches | drop failures | max drop gap | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 64 | 9 | 5 | 1.800000 | 0 | 128 | 448 | PASS_EQUIV_NEGATIVE_CONTROL |
| 2 | 256 | 9 | 5 | 1.800000 | 0 | 512 | 512 | PASS_EQUIV_NEGATIVE_CONTROL |
| 4 | 64 | 25 | 9 | 2.777778 | 0 | 253 | 672 | PASS_EQUIV_NEGATIVE_CONTROL |
| 4 | 256 | 25 | 9 | 2.777778 | 0 | 1009 | 1032 | PASS_EQUIV_NEGATIVE_CONTROL |
| 6 | 64 | 49 | 13 | 3.769231 | 0 | 384 | 912 | PASS_EQUIV_NEGATIVE_CONTROL |
| 6 | 256 | 49 | 13 | 3.769231 | 0 | 1529 | 1360 | PASS_EQUIV_NEGATIVE_CONTROL |

## Interpretation

The lane-local arithmetic model matches the dense reference on every
tested coefficient, and the current-format drop-offlane control fails.
This preserves the Stage112 warning: body-linear skipping needs a new
selector/key or ciphertext format. It still does not prove a full SAB
optimization.
