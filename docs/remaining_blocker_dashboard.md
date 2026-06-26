# Remaining Blocker Dashboard

Date: 2026-06-26

## Purpose

This dashboard aggregates the remaining stronger-claim blockers after the
scoped PVW/MAT-SAB engineering evidence chain has closed. It is a
reproducibility/control-plane artifact only: it does not change scalar
SAB, `sab_pvw_*`, benchmark results, or claim labels.

## Dashboard

| blocker | status | blocking condition | unlock command | claim policy |
|---|---|---|---|---|
| CB5 | final_A8=BLOCKED_EXTERNAL; cb5=BLOCKED_EXTERNAL; stage44_perf=BLOCKED; external_perf=MISSING | Native Linux/perf hardware-counter evidence is not available in the current WSL2 environment. | `STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh` | Do not claim theoretical MAT-AVX512 optimality or load/store superiority without native/perf evidence and manual interpretation. |
| CB6 | cb6=BLOCKED_EXTERNAL_REVIEW; related=SCOPED_RELATED_WORK_REFRESHED__NOVELTY_STILL_BLOCKED; novelty_gate=BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW | Related-work source access is refreshed, but manual full-text claim-to-source review is still missing. | `FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh` | Keep the contribution framed as scoped engineering/systems evidence until novelty review is complete. |
| CB7 | final_A8b=EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED; cb7=EXTERNAL_FULLTEXT_REVIEW_REQUIRED; stage44_fulltext=BLOCKED; stage55_fulltext=BLOCKED; stage55_metadata=PASS; stage55_decision=WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW; stage72_fulltext=WAIT_FULLTEXT_ARTIFACT; stage72_author=PASS; stage72_decision=PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED; related_fulltext=BLOCKED_FULLTEXT; external_fulltext=AVAILABLE_UNREVIEWED | A 2025/686 full-text artifact is registered and hashed, but manual claim-to-source review is still incomplete. | `Complete repro/stage38_fulltext_review_gate/review_checklist.csv with concrete paper anchors.` | Do not cite theorem, algorithm, table, figure, or experiment numbers from 2025/686 until full text is supplied and reviewed. |
| A9 | final_A9=SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED; stage44_decision=WAIT_EXTERNAL_UNLOCKS; stage41_final=READY_AFTER_UNLOCKS | The scoped engineering chain is ready, but stronger claims remain blocked by the rows above. | `FINAL_RECHECK_CITATION=1 FINAL_RECHECK_RELATED_WORK=1 FINAL_RECHECK_STAGE44_REPROBE=1 bash scripts/run_final_goal_recheck.sh` | Keep the final status scoped/review-required until CB5/CB6/CB7 are resolved or the goal scope is explicitly narrowed. |

## Decision

The project remains in the scoped engineering-ready state. The remaining
work is external evidence and manual review for stronger claims, not a
local SAB implementation blocker.
