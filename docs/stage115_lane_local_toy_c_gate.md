# Stage115 Lane-Local Toy C Gate

Date: 2026-07-03

## Decision

`PASS_STAGE115_TOY_C_LAYOUT_FEASIBLE_PROTOTYPE_REQUIRED`

Stage115 builds and runs a generated C layout probe. It measures the
current dense shared-mask toy layout against the lane-local multimask
toy layout for r=2/4/6/8 and N=2048/4096.

This is a representation/resource gate only. It does not prove
cryptographic correctness, noise safety, AVX512 optimality, or complete
SAB speedup.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage115_compile | PASS | gcc_compile | true | Toy C layout probe compiled and executed under WSL gcc. |
| stage115_layout_matrix | PASS | rows | 8 | r=2/4/6/8 and N=2048/4096 current-vs-lane-local rows are measured. |
| stage115_target_r4_resource | PASS_BOUNDED | r4_N2048_requested_ratio | 1.100000 | Target r=4 lane-local toy layout requested-byte overhead is bounded. |
| stage115_r2_lower_bound_control | PASS_BOUNDED | r2_N2048_requested_ratio | 1.333333 | r=2 is the worst small-r resource control and remains within the configured 1.50 cap. |
| stage115_decision | PASS_STAGE115_TOY_C_LAYOUT_FEASIBLE_PROTOTYPE_REQUIRED | next_gate_policy |  | Toy C layout evidence does not kill lane-local multimask, but no correctness/noise/performance claim is made. |

## Layout Ratios

| r | N | requested ratio | RSS ratio | product ratio | product/requested | status |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 2048 | 1.333333 | 1.026961 | 1.800000 | 1.350000 | LAYOUT_NOT_FATAL |
| 4 | 2048 | 1.100000 | 0.995868 | 2.777778 | 2.525253 | LAYOUT_NOT_FATAL |
| 6 | 2048 | 0.914286 | 0.942997 | 3.769231 | 4.122596 | LAYOUT_NOT_FATAL |
| 8 | 2048 | 0.777778 | 0.905080 | 4.764706 | 6.126050 | LAYOUT_NOT_FATAL |
| 2 | 4096 | 1.333333 | 1.140206 | 1.800000 | 1.350000 | LAYOUT_NOT_FATAL |
| 4 | 4096 | 1.100000 | 1.000000 | 2.777778 | 2.525253 | LAYOUT_NOT_FATAL |
| 6 | 4096 | 0.914286 | 1.051665 | 3.769231 | 4.122596 | LAYOUT_NOT_FATAL |
| 8 | 4096 | 0.777778 | 0.875433 | 4.764706 | 6.126050 | LAYOUT_NOT_FATAL |

## Interpretation

For the target r=4, N=2048 control row, the conservative lane-local
toy layout has bounded requested-byte overhead while reducing the
product-term model from dense 25 to 9. That keeps the branch alive for
a toy arithmetic equivalence prototype. It is not enough evidence to
touch the MOSFHET hot path.
