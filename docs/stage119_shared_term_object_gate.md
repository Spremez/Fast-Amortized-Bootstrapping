# Stage119 Shared-Term Object Gate

Date: 2026-07-03

## Decision

`PASS_STAGE119_VECTOR_SHARED_OBJECT_READY_REAL_STRUCT_PROTOTYPE_REQUIRED`

Stage119 checks a real-object semantic risk: whether the shared row can
be scalar-shared across independent LUT lanes. It cannot. The scalar
shared interpretation is rejected, and the vector-shared lane-local
object is selected for future real struct work.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage119_compile | PASS | gcc_compile | true | Generated shared-term object C probe compiled under WSL gcc. |
| stage119_scalar_shared_negative_control | PASS_REJECTED | scalar_negative_failures | 59;240;178;727;301;1205 | A scalar shared term cannot represent independent lane shared messages. |
| stage119_vector_shared_phase | PASS | vector_mismatches | 0;0;0;0;0;0 | Vector-shared lane-local object matches dense reference in noiseless phase. |
| stage119_noise_bound | PASS_BOUNDED | noise_bound_violations | 0;0;0;0;0;0 | Toy noise remains within the digit-sum bound. |
| stage119_layout_refinement | PASS | r4_vector_over_dense_byte_ratio | 0.800000 | Vector-shared object is no larger than the Stage118 conservative shape and remains below dense bytes for r=4. |
| stage119_decision | PASS_STAGE119_VECTOR_SHARED_OBJECT_READY_REAL_STRUCT_PROTOTYPE_REQUIRED | next_gate_policy |  | Shared-term semantics are refined: scalar-shared is rejected, vector-shared is the only viable object route. |

## Phase Results

| r | N | variant | mismatches | negative failures | max noise | noise bound | violations | status |
|---:|---:|---|---:|---:|---:|---:|---:|---|
| 2 | 64 | scalar_shared | 59 | 59 | 0 | 0 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 2 | 64 | vector_shared | 0 | 0 | 17 | 18 | 0 | PASS_VECTOR_OBJECT |
| 2 | 256 | scalar_shared | 240 | 240 | 0 | 0 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 2 | 256 | vector_shared | 0 | 0 | 18 | 18 | 0 | PASS_VECTOR_OBJECT |
| 4 | 64 | scalar_shared | 178 | 178 | 0 | 0 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 4 | 64 | vector_shared | 0 | 0 | 17 | 18 | 0 | PASS_VECTOR_OBJECT |
| 4 | 256 | scalar_shared | 727 | 727 | 0 | 0 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 4 | 256 | vector_shared | 0 | 0 | 18 | 18 | 0 | PASS_VECTOR_OBJECT |
| 6 | 64 | scalar_shared | 301 | 301 | 0 | 0 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 6 | 64 | vector_shared | 0 | 0 | 17 | 18 | 0 | PASS_VECTOR_OBJECT |
| 6 | 256 | scalar_shared | 1205 | 1205 | 0 | 0 | 0 | PASS_REJECTED_SCALAR_SHARED |
| 6 | 256 | vector_shared | 0 | 0 | 18 | 18 | 0 | PASS_VECTOR_OBJECT |

## Layout Refinement

| r | N | dense terms | scalar terms | vector terms | vector/dense bytes | vector product ratio | status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 64 | 9 | 5 | 4 | 1.000000 | 2.250000 | PASS_LAYOUT_REFINED |
| 2 | 256 | 9 | 5 | 4 | 1.000000 | 2.250000 | PASS_LAYOUT_REFINED |
| 4 | 64 | 25 | 9 | 8 | 0.800000 | 3.125000 | PASS_LAYOUT_REFINED |
| 4 | 256 | 25 | 9 | 8 | 0.800000 | 3.125000 | PASS_LAYOUT_REFINED |
| 6 | 64 | 49 | 13 | 12 | 0.642857 | 4.083333 | PASS_LAYOUT_REFINED |
| 6 | 256 | 49 | 13 | 12 | 0.642857 | 4.083333 | PASS_LAYOUT_REFINED |

## Interpretation

This is a correction, not a final acceleration claim. The valid object
route is vector-shared lane-local storage. Stage120 must build real C
structs and real polynomial phase/noise tests outside `sab_pvw_*`.
