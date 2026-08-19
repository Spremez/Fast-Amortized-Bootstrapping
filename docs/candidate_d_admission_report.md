# Candidate D Admission Report

## Decision

`BLOCK_CANDIDATE_D_INCOMPLETE_EVIDENCE`

Candidate D remains active at D2_OPERATOR_CLOSURE_PASS; the research goal is externally blocked, Candidate E remains reserved, and production hot-path permission is false.

## Recomputed Gate Chain

| gate | status | decision/evidence |
| --- | --- | --- |
| D0 baseline freeze | PASS | `PASS_D0_CANDIDATE_D_BASELINES_FROZEN` |
| D1 novelty/full-text audit | PASS | `PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE` |
| D2 exact operator closure | PASS | `PASS_D2_OPERATOR_CLOSURE_G_LE_4` |
| D2 deterministic replay | PASS | canonical scientific runner required |
| D2 gamma / negative controls | 2 | `PASS` |
| D3 deterministic replay | NOT_REACHED | canonical scientific runner required |
| D3 integer binding | BLOCK | canonical D3 source evidence |
| D3 standard security objects | BLOCK | canonical D3 source evidence |
| D3 absolute noise/decode | BLOCK | canonical D3 source evidence |
| D3 complete cost / resource | BLOCK / BLOCK | canonical D3 source evidence; pessimistic speedup `missing` |

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
decision is bound to input commit `0d02637d9c702eac28079738e6b45b8c5401e459`, controller commit
`cfb8f6330e6cafecc60db48e9f341af578debe14`, immutable historical BLOCK commit
`fba794ce8820fb2ab167bf928c9cdae67ed508b9`, predecessor evidence commit
`2e2508a4716f83a92d9b53e7b716569c642c1033` with controller
`fd5043edb7128e4b5f7bb86ddfdd948c88f53fd0` and decision-evidence SHA-256
`2e25282ede5c6339f2e2ccd4ccc835d3eeb2f6216c0330049902600f06a14c8f`, run date `2026-08-19`,
execution platform `Windows-WSL; CPython-3.12; evidence-controller-only; no-performance-claim`, and decision-evidence hash
`ae31e8176c31e7f5fb51e70f1a4d8cb8a00a81cb93219b8fe8c2b2f55eb175bf`.

## Finite Resume Condition

Implement or repair the canonical Tasks 7-8 D3 generator, fixed noise/security anchors, frozen B1 profile binding, and complete cost/resource model under docs/candidate_d_task9_replay_contract.md; run python scripts/run_candidate_d_d3_admission.py --root <absolute-repository-root> --output-root <staging-output-directory> --input-commit <last-valid-stage-commit> --controller-commit cfb8f6330e6cafecc60db48e9f341af578debe14; install the verified outputs, commit the canonical D3 artifacts as <new-D3-commit>, then rerun Task 9 with git show cfb8f6330e6cafecc60db48e9f341af578debe14:scripts/candidate_d_task9_launcher.py | python -I -S - --mode run --root . --input-commit <new-D3-commit> --controller-commit cfb8f6330e6cafecc60db48e9f341af578debe14 --run-date <YYYY-MM-DD> --execution-platform "<audited-evidence-platform>"; git show cfb8f6330e6cafecc60db48e9f341af578debe14:scripts/candidate_d_task9_launcher.py | python -I -S - --mode apply --root . --input-commit <new-D3-commit> --controller-commit cfb8f6330e6cafecc60db48e9f341af578debe14 --run-date <YYYY-MM-DD> --execution-platform "<audited-evidence-platform>".
