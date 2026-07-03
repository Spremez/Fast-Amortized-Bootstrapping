# Stage157 Sub-Decompose Fusion Preflight

Decision: `PASS_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_POSITIVE_IMPLEMENTATION_CANDIDATE`

Stage157 tests an isolated same-format candidate after Stage156 rejects naive
DFT-only state: compute `decompose(in2-in1)` directly instead of first writing
the `sub` PVW_TMLWE and then decomposing it. This is a standalone C microbench;
it does not alter production code.

## Correctness

| case | status | mismatches | first_mismatch |
| --- | --- | --- | --- |
| target_r6_N2048_l1_bg23 | PASS | 0 | -1 |
| control_r4_N2048_l1_bg23 | PASS | 0 | -1 |
| control_r6_N2048_l2_bg8 | PASS | 0 | -1 |

## Microbench

| case | components | N | Bg_bit | l | reps | separate_ns | fused_ns | speedup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_r6_N2048_l1_bg23 | 7 | 2048 | 23 | 1 | 8000 | 15000.000 | 13750.000 | 1.090909 |
| control_r4_N2048_l1_bg23 | 5 | 2048 | 23 | 1 | 10000 | 11300.000 | 9800.000 | 1.153061 |
| control_r6_N2048_l2_bg8 | 7 | 2048 | 8 | 2 | 5000 | 29400.000 | 30200.000 | 0.973510 |

## Decision

| gate | status | metric | value | next_action |
| --- | --- | --- | --- | --- |
| stage157_build | PASS | gcc | D:\programs\LLVM\bin\gcc.EXE | Install/use gcc before interpreting microbench if blocked. |
| stage157_correctness | PASS | mismatches | 0;0;0 | Do not implement if any mismatch appears. |
| stage157_microbench | PASS | target_speedup | 1.090909 | Only open production implementation if target speedup exceeds preflight threshold. |
| stage157_decision | PASS_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_POSITIVE_IMPLEMENTATION_CANDIDATE | candidate_route | sub_decompose_fusion | If positive, add an explicit MAT EP from precomputed decomposed-difference path; otherwise route to compact/cache work. |

Interpretation: this preflight targets memory traffic around `pvmtmlwe_sub`
and dense `pvmtmlwe_decompose`, not the DFT or MAT addmul itself. A positive
result is only permission to implement a guarded production path and rerun
complete SAB `T_bootstrap/r`.
