# Stage92 External Unlock Execution Packet

Date: 2026-06-26

## Decision

`PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED`

External unlock execution packet is recorded; stronger claims remain blocked until external evidence is supplied and reviewed.

Stage92 is an execution handoff for remaining external blockers. It does
not run native perf, does not fetch or review the 2025/686 full text,
and does not upgrade the Stage91 scoped final package.

## Gates

| gate | status | evidence | detail | next action |
|---|---|---|---|---|
| stage92_stage91_precondition | PASS | repro/stage91_final_package/summary.csv | stage91_decision=PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED | Rerun Stage91 before relying on Stage92 if this gate fails. |
| stage92_unlock_sources | PASS | repro/remaining_blocker_dashboard.csv; repro/stage52_external_unlock_readiness.csv | missing_blockers=none; missing_unlocks=none | Restore Stage52/blocker rows before executing external unlock commands. |
| stage92_lane_packet | PASS_EXTERNAL_LANES_RECORDED | repro/stage92_external_unlock_execution/lane_matrix.csv | lanes=native_perf:READY_EXTERNAL_EXECUTION; fulltext_686:READY_EXTERNAL_EXECUTION; novelty_review:READY_EXTERNAL_EXECUTION; final_recheck:READY_EXTERNAL_EXECUTION | Execute the lane commands only on the required external platform or with supplied full-text artifacts. |
| stage92_claim_guard | PASS_STRONGER_CLAIMS_BLOCKED | repro/stage91_final_package/claim_boundary.csv | Stage91 blocked C3/C4/C5 stronger claims remain blocked. | Do not upgrade claim wording until the Stage92 acceptance matrix passes. |
| stage92_decision | PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED | repro/stage92_external_unlock_execution/summary.csv | External unlock execution packet is recorded; stronger claims remain blocked until external evidence is supplied and reviewed. | Run only the relevant external unlock lane, then rerun Stage90/91/92/42 verification before changing claims. |

## Unlock Lanes

| lane | blocker | readiness | command | packet status |
|---|---|---|---|---|
| native_perf | CB5 | WAIT_NATIVE_PERF | `STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh` | READY_EXTERNAL_EXECUTION |
| fulltext_686 | CB7 | WAIT_EXTERNAL_FULLTEXT | `FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh` | READY_EXTERNAL_EXECUTION |
| novelty_review | CB6 | WAIT_MANUAL_FULLTEXT_REVIEW | `FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh` | READY_EXTERNAL_EXECUTION |
| final_recheck | A9 | WAIT_UNLOCKS | `FINAL_RECHECK_CITATION=1 FINAL_RECHECK_PERF=1 FINAL_RECHECK_EXTERNAL_INTAKE=1 bash scripts/run_final_goal_recheck.sh` | READY_EXTERNAL_EXECUTION |

## Commands

| command | environment | pass condition | claim effect |
|---|---|---|---|
| `STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh` | native Linux or perf-enabled WSL with target AVX512 hardware | summary.csv records hardware_counter_gate=PASS and bench_correctness=PASS. | Only moves CB5/A8 to review-required; manual interpretation is still required before theoretical-optimality wording. |
| `FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh` | local environment with reviewed 2025/686 PDF or text artifact | Stage38 reports FULLTEXT_AVAILABLE_REVIEW_REQUIRED or stronger and the artifact hash is registered. | Only moves CB7/A8b to review-required; theorem-level citations remain blocked until source anchors are written. |
| `FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf STAGE28_NATIVE_PERF_SUMMARY=/path/to/summary.csv python scripts/register_external_evidence.py` | local environment after collecting full text or native perf artifacts | External intake rows are non-missing and contain path, size, hash, and status. | Registration enables review gates; it never upgrades a claim alone. |
| `FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh` | local environment with full-text anchors for 2025/686 and related work | Novelty gate no longer reports BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW. | Only after manual source-anchor review may novelty wording move beyond scoped engineering/systems wording. |
| `FINAL_RECHECK_CITATION=1 FINAL_RECHECK_PERF=1 FINAL_RECHECK_EXTERNAL_INTAKE=1 FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh && bash scripts/run_stage90_external_claim_unlock.sh && bash scripts/run_stage91_final_package.sh` | local environment after external artifacts and manual reviews are complete | A8/A8b/CB5/CB6/CB7 are no longer blocked and claim wording has been manually checked. | Only this path can support moving beyond the Stage91 scoped package. |

## Acceptance Matrix

| id | requirement | pass condition | decision effect |
|---|---|---|---|
| A92-CB5 | Native/perf-backed MAT-AVX512 attribution. | hardware_counter_gate=PASS, bench_correctness=PASS, and manual interpretation ties counters to the MAT path. | Keep theoretical optimality blocked unless pass_condition is met. |
| A92-CB7 | 2025/686 full-text protocol/theorem citation review. | Full text is registered and protocol stages, complexity formulas, noise/security assumptions, and tables/figures are mapped to anchors. | Keep theorem/table/figure/experiment citations blocked unless pass_condition is met. |
| A92-CB6 | Novelty and related-work distinction review. | Every novelty/distinction sentence maps to reviewed source anchors and the novelty gate is no longer blocked. | Keep novelty wording scoped to engineering/systems evidence unless pass_condition is met. |
| A92-A9 | Final claim upgrade beyond scoped engineering. | CB5, CB6, and CB7 are no longer blocked; final audit upgrades A9; Stage42 verifier passes from a clean worktree. | Keep the active goal open and scoped if any fail_condition remains. |
