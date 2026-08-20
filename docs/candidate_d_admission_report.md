# Candidate D Admission Report

## Decision

`ADMIT_CANDIDATE_D_TO_ISOLATED_ENCRYPTED_OPERATOR_IMPLEMENTATION`

Candidate D advances to D3_ADMISSION_PASS, remains active, and receives permission only for a separate opt-in D4 isolated encrypted-operator experiment. Scalar defaults are unchanged.

## Recomputed Gate Chain

| gate | status | decision/evidence |
| --- | --- | --- |
| D0 baseline freeze | PASS | `PASS_D0_CANDIDATE_D_BASELINES_FROZEN` |
| D1 novelty/full-text audit | PASS | `PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE` |
| D2 exact operator closure | PASS | `PASS_D2_OPERATOR_CLOSURE_G_LE_4` |
| D2 deterministic replay | PASS | canonical scientific runner required |
| D2 gamma / negative controls | 2 | `PASS` |
| D3 deterministic replay | PASS | canonical scientific runner required |
| D3 integer binding | PASS | canonical D3 source evidence |
| D3 standard security objects | PASS | canonical D3 source evidence |
| D3 absolute noise/decode | PASS | canonical D3 source evidence |
| D3 complete cost / resource | PASS / PASS | canonical D3 source evidence; pessimistic speedup `1.459858916315` |

D0 was regenerated from the pinned baseline anchors and compared byte for
byte with the tracked D0 artifacts. D1 was regenerated from the source
registry and locally hash-bound full texts and compared byte for byte with the
tracked D1 artifacts. Missing D1 reviews: `none`. D2 and D3 PASS/REJECT
values have authority only after their reviewed, commit-pinned canonical
runner executes under the finite threat model in a temporary output root and
every artifact compares byte for byte. Static CSV parsing is secondary;
skipped or hand-written values are never promoted.

## Replay Claim Boundary

This controller authenticates reviewed deterministic execution, not arbitrary
untrusted code. Mandatory source review of the canonical runner and its exact
recursive local closure is a prerequisite for scientific authority. Task 9
authority begins with the launcher blob read from the controller commit and
executed under `python -I -S`. It authenticates a composite tree based at the
input commit with the complete controller execution closure overlaid before
any repository import; the caller root remains an untrusted evidence/output
destination. Plain mutable-worktree run/apply entrypoints are not
authoritative. The
import guard, execution audit, checkout snapshot, output-tree validation, and
completion attestation are defense in depth, not a hostile-code sandbox. A
malicious commit-pinned runner and arbitrary native code are out of scope; see
`docs/candidate_d_task9_threat_model.md`.

## Scope

No D0-D3 terminal route is itself a complete SAB speedup or paper claim. The
decision is bound to input commit `efc47d9485216b47fbfbfbbc0d8a278580401c38`, controller commit
`efc47d9485216b47fbfbfbbc0d8a278580401c38`, immutable historical BLOCK commit
`fba794ce8820fb2ab167bf928c9cdae67ed508b9`, predecessor evidence commit
`2e2508a4716f83a92d9b53e7b716569c642c1033` with controller
`fd5043edb7128e4b5f7bb86ddfdd948c88f53fd0` and decision-evidence SHA-256
`2e25282ede5c6339f2e2ccd4ccc835d3eeb2f6216c0330049902600f06a14c8f`, run date `2026-08-20`,
execution platform `Windows-WSL; CPython-3.12; evidence-controller-only; no-performance-claim`, and decision-evidence hash
`209b595ed6b0220284c2e832978de5f447367fb7c0636043a1ef2ee7a9ef901b`.
