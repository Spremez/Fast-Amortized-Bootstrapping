# Stage120 Real Struct Phase/Noise Gate

Date: 2026-07-03

## Decision

`PASS_STAGE120_REAL_STRUCT_PHASE_NOISE_READY_DFT_PROTOTYPE_REQUIRED`

Stage120 builds a standalone vector-shared real C struct prototype with
polynomial arrays and negacyclic phase decryption. It remains outside
`sab_pvw_*` and MOSFHET hot paths.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage120_compile | PASS | gcc_compile | true | Generated real C struct polynomial prototype compiled under WSL gcc. |
| stage120_phase_equivalence | PASS | mismatches_noiseless | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Negacyclic-polynomial phase decrypts match vector-shared reference across all seeds. |
| stage120_noise_bound | PASS_BOUNDED | noise_bound_violations | 0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0 | Injected coefficient noise stays within digit-sum bounds. |
| stage120_layout_allocation | PASS | r4_N64_vector_over_dense_poly_ratio | 0.533333 | Real struct allocation model preserves the vector-shared layout bound. |
| stage120_decision | PASS_STAGE120_REAL_STRUCT_PHASE_NOISE_READY_DFT_PROTOTYPE_REQUIRED | next_gate_policy |  | Real structs pass polynomial phase/noise gate outside SAB. |

## Layout Rows

| r | N | dense terms | vector terms | poly ratio | requested bytes | status |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 32 | 9 | 4 | 0.666667 | 2768 | PASS_LAYOUT |
| 2 | 64 | 9 | 4 | 0.666667 | 5328 | PASS_LAYOUT |
| 4 | 32 | 25 | 8 | 0.533333 | 5488 | PASS_LAYOUT |
| 4 | 64 | 25 | 8 | 0.533333 | 10608 | PASS_LAYOUT |
| 6 | 32 | 49 | 12 | 0.428571 | 8208 | PASS_LAYOUT |
| 6 | 64 | 49 | 12 | 0.428571 | 15888 | PASS_LAYOUT |

## Phase/Noise Rows

| r | N | seed | mismatches | max noise | bound | violations | rss KB | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 32 | 0 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 32 | 1 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 32 | 2 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 32 | 3 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 32 | 4 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 64 | 0 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 64 | 1 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 64 | 2 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 64 | 3 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 2 | 64 | 4 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 32 | 0 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 32 | 1 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 32 | 2 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 32 | 3 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 32 | 4 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 64 | 0 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 64 | 1 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 64 | 2 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 64 | 3 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 4 | 64 | 4 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 32 | 0 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 32 | 1 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 32 | 2 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 32 | 3 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 32 | 4 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 64 | 0 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 64 | 1 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 64 | 2 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 64 | 3 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |
| 6 | 64 | 4 | 0 | 6 | 6 | 0 | 1004 | PASS_REAL_STRUCT_PHASE_NOISE |

## Interpretation

This advances the valid vector-shared route from object semantics to a
real C polynomial struct prototype. It still does not provide DFT,
external-product kernel, SAB schedule, complete-SAB correctness, or
performance evidence.
