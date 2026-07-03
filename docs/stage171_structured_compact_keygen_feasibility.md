# Stage171 Structured Compact Keygen Feasibility

Decision: `PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY`.

Stage171 is a bounded research gate. It does not implement compact SAB. It
separates three claims that were previously easy to mix:

- ciphertext-exact replacement of dense MAT: still blocked;
- structured logical selector compactness: finite-field feasible under explicit
  zero-cross constraints;
- secure/noise-bounded bootstrapping key distribution: open proof work.

The practical reason to keep this route alive is that r=6 dense MAT uses 49
selector terms while a structured compact map would use 19 logical terms. Using
Stage170's current component timings, the idealized r=6 component-only upper
bound is recorded in `speed_projection.csv`; it is not a benchmark.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage171_inputs | PASS | stage170_run_metrics | present | repro/stage170_native_split_counter_microbench/run_metrics.csv | Stage171 uses Stage170 component timings for bounded speed projection. | Do not compute projection without Stage170. |
| stage171_structured_finite_check | PASS | finite_trials | 64 | repro/stage171_structured_compact_keygen_feasibility/finite_field_structured_checks.csv | Structured matrices project exactly; random dense matrices still expose missing cross terms. | Only structured keygen can reopen compact SAB. |
| stage171_projection | PASS | r6_upper_component_speedup | 1.665316530 | repro/stage171_structured_compact_keygen_feasibility/speed_projection.csv | Projection assumes MAT EP scales with term count and from_DFT remains unchanged. | Treat as upper-bound routing evidence, not a benchmark result. |
| stage171_proof_obligations | BLOCKED_PROOF | open_obligations | 5 | repro/stage171_structured_compact_keygen_feasibility/proof_obligations.csv | Keygen distribution, phase invariant, noise, security, and closed-state API remain open. | No compact SAB implementation or paper claim before these are resolved. |
| stage171_decision | PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY | structured_compact_route | proof_route_only | repro/stage171_structured_compact_keygen_feasibility/summary.csv | Stage171 converts compact optimization into bounded proof obligations instead of theory drift. | Run Stage172 closeout or explicitly choose Stage173 proof work. |

## Algebraic Constraints

| r | state_polys | dense_terms | structured_terms | omitted_body_cross_terms | term_reduction_factor | required_constraint | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 3 | 9 | 7 | 2 | 1.285714286 | M[q,j]=0 for q!=j and q,j>0 at the logical selector level | STRUCTURED_ONLY_NOT_GENERIC |
| 4 | 5 | 25 | 13 | 12 | 1.923076923 | M[q,j]=0 for q!=j and q,j>0 at the logical selector level | STRUCTURED_ONLY_NOT_GENERIC |
| 6 | 7 | 49 | 19 | 30 | 2.578947368 | M[q,j]=0 for q!=j and q,j>0 at the logical selector level | STRUCTURED_ONLY_NOT_GENERIC |
| 8 | 9 | 81 | 25 | 56 | 3.240000000 | M[q,j]=0 for q!=j and q,j>0 at the logical selector level | STRUCTURED_ONLY_NOT_GENERIC |

## Claim Levels

| level | claim | status | reason | allowed_next |
| --- | --- | --- | --- | --- |
| ciphertext_exact_dense_MAT | Compact lane-local data equals the existing dense MAT ciphertext map. | BLOCKED_BY_STAGE166 | Generic dense encrypted selector includes body-to-body cross terms. | Do not replace dense MAT with compact storage under this claim. |
| logical_selector_exact | A new structured keygen enforces zero logical body cross terms. | FINITE_FIELD_FEASIBLE | Stage171 finite checks show compact projection is exact under explicit structural constraints. | Write formal keygen, phase, and noise equations before implementation. |
| phase_correct_under_decryption | Omitting encryptions of logical zero cross terms preserves decrypted message and changes only noise/distribution. | PROOF_REQUIRED | Dropping encrypted zero samples changes bootstrapping-key distribution and noise accounting. | Run finite/noise toy checks only after equations specify the distribution. |
| complete_SAB_speedup | Structured compact keygen accelerates full SAB. | BLOCKED_IMPLEMENTATION | No structured keygen, SAB integration, correctness/noise, or full A/B benchmark exists. | Keep complete-SAB speedup claims tied to Stage169 until this route is implemented and measured. |

## Finite Check Sample

| r | trial | field_prime | structured_mismatches | dense_mismatches | expected_dense_missing | status |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 1 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 2 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 3 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 4 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 5 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 6 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 7 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 8 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 9 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 10 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |
| 2 | 11 | 65537 | 0 | 2 | 2 | PASS_STRUCTURED_EXACT_DENSE_BLOCKED |

Full finite checks are in `repro/stage171_structured_compact_keygen_feasibility/finite_field_structured_checks.csv`.

## Proof Obligations

| obligation | required_result | blocking_question | gate | status |
| --- | --- | --- | --- | --- |
| keygen_distribution | Define a bootstrapping-key distribution with zero logical body cross terms and compact public representation. | Are omitted zero-encryption samples safely public zeros, or must they be simulated under RLWE? | formal equations plus toy sampler; no SAB code before this passes | OPEN |
| phase_invariant | For every CMUX/NCMUX step, prove each output lane decrypts to the same logical phase as scalar SAB for independent LUT lanes. | Does RGSW monomial rotation preserve the structured selector constraint at every sparse schedule step? | symbolic phase derivation plus finite-field phase test | OPEN |
| noise_accounting | Bound noise after deleting or resampling cross zero terms and compare with dense MAT baseline. | Does the structured distribution reduce noise, leave it comparable, or introduce correlations that hurt correctness? | multi-seed noise simulation before full SAB benchmark | OPEN |
| security_reduction | State whether security follows from standard RLWE samples, a hybrid replacing zero encryptions, or a new structured assumption. | Can a distinguisher exploit missing body-to-body ciphertext components in the public bootstrapping key? | written reduction or explicit assumption before paper-level novelty claim | OPEN |
| closed_state_API | Specify whether compact state remains a PVW_TMLWE-compatible closed state through SAB sparse_mul and extract. | Can from_DFT/extract consume the compact output without re-expanding to dense MAT? | interface design and isolated phase equivalence test | OPEN |

## Speed Projection

| r | dense_terms | structured_terms | term_reduction_factor | stage170_mat_ep_us | stage170_from_dft_us | ideal_structured_mat_us | component_baseline_us | ideal_component_us | upper_component_speedup | scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 9 | 7 | 1.285714286 |  |  |  |  |  |  | upper-bound model only; excludes proof, keygen, from_DFT count, extract/KS, memory layout, and full SAB effects |
| 4 | 25 | 13 | 1.923076923 |  |  |  |  |  |  | upper-bound model only; excludes proof, keygen, from_DFT count, extract/KS, memory layout, and full SAB effects |
| 6 | 49 | 19 | 2.578947368 | 66.127151855 | 35.211114746 | 25.641140515 | 101.338266601 | 60.852255261 | 1.665316530 | upper-bound model only; excludes proof, keygen, from_DFT count, extract/KS, memory layout, and full SAB effects |
| 8 | 81 | 25 | 3.240000000 |  |  |  |  |  |  | upper-bound model only; excludes proof, keygen, from_DFT count, extract/KS, memory layout, and full SAB effects |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 172 | frontier closeout after Stage169/170/171 | Stage171 keeps structured compact as proof route, not implementation-ready code. | Refresh allowed claims, next engineering route, and proof-route decision boundary. | No final theoretical-optimality or compact-SAB claim without proof and full benchmark. |
| P1 | 173 | structured compact formal phase/noise toy | Only if the project chooses to pursue a new keygen/security route. | Write exact equations and finite/noise toy sampler for the structured compact distribution. | If equations do not close, reject compact route before implementation. |
| P2 | 174 | from_DFT locality experiment | Stage170 shows from_DFT has high cache-miss and load/store pressure. | Bounded microbench with layout/scratch changes and full-SAB A/B only if microbench wins. | Do not promote a backend-only improvement without complete-SAB endpoint. |
