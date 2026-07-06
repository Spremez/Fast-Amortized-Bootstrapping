# Stage337 Frontier Correction Report

Decision: `PASS_STAGE337_FRONTIER_CORRECTED_NO_REPEAT_FAILED_CANDIDATES`.

Stage336 selected direct IFFT lifecycle as the apparent closed-path frontier.
Stage337 corrects that route by consuming the earlier Stage318/319 IFFT
microbenches, Stage312/313 digit evidence, Stage321 r4-unrolled full-SAB A/B,
Stage325 selector-transpose probe, and Stage326 closeout.

## Summary

| decision | corrected_stage336_candidate | exact_dense_frontier | compact_frontier | allowed_next |
| --- | --- | --- | --- | --- |
| PASS_STAGE337_FRONTIER_CORRECTED_NO_REPEAT_FAILED_CANDIDATES | direct_ifft_lifecycle_closed_by_stage318_319 | closed_under_current_evidence | blocked_proof_required | new_mechanism_or_formal_proof_or_scoped_package |

## Closed Candidate Audit

| candidate | status | reason | reopen_condition |
| --- | --- | --- | --- |
| direct_ifft_batch5_intrinsics | CLOSED_SLOW | Correct but slower isolated batch5 intrinsics; do not integrate. | Different backend primitive with isolated speedup and equivalence. |
| direct_ifft_batch5_asm | CLOSED_SLOW | Correct but slower hand assembly; closes batch5 IFFT family. | New SPQLIOS primitive or native evidence not equivalent to Stage319. |
| digit_narrow32 | CLOSED_FULLSAB_NEUTRAL | Microbench positive but complete SAB A/B neutral. | New digit mechanism with full-SAB positive A/B. |
| r4_unrolled_rows | CLOSED_FULLSAB_NEUTRAL | Current direct baseline comparison ratio=0.998571. | New load/store count mechanism beyond pointer hoisting. |
| selector_transpose | CLOSED_MICRO_NEUTRAL | Isolated dense speedup below threshold for 1% full-SAB projection. | Different key layout with resource proof and stronger isolated speedup. |
| compact_selector_current_state | DENIED_COMPLETE_SAB | Current compact/lane-local state does not support complete selector integration. | Formal neighbor-capable closed state plus keygen/security/noise gates. |

## Route Decision

| route | decision | basis | allowed_next |
| --- | --- | --- | --- |
| repeat_old_exact_kernel_work | DENY | Stage318/319/312/321/325 already close the concrete candidates. | none |
| new_exact_mechanism | ALLOW_IF_MECHANISM_EXISTS | Stage326 permits reopening only with a new load/store/count mechanism. | preflight proof plus isolated microbench before SAB code |
| compact_or_structured_algorithm | ALLOW_PROOF_ONLY | Stage335/222 deny current complete selector route. | formal closed-state/keygen/noise proof before any hot-path code |
| claim_and_parameter_package | ALLOW | Current supported claim remains scoped T_bootstrap/r evidence. | parameter/statistical refresh or paper package without stronger wording |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage336_input | PASS | Stage336 frontier | present |
| G2_no_repeat_candidates | PASS | closed candidate families | ifft;digit;r4_unrolled;selector_transpose |
| G3_exact_dense_closeout | PASS | Stage326 frontier | closed_under_current_evidence |
| G4_compact_boundary | PASS | Stage335 compact | denied |
| G5_decision | PASS_STAGE337_FRONTIER_CORRECTED_NO_REPEAT_FAILED_CANDIDATES | stage decision | no_repeat_failed_candidates |
