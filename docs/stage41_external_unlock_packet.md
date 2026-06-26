# Stage 41 External Unlock Packet

Date: 2026-06-26

## Purpose

Stage 41 turns the remaining external blockers into executable gates.
It does not change scalar SAB, the promoted `sab_pvw_*` path, or any
claim label by itself. It records what must be supplied and reviewed
before the project can move beyond the current scoped engineering result.

## Unlock Matrix

| unlock | readiness | current status | command | review gate |
|---|---|---|---|---|
| S41-FULLTEXT-INTAKE | READY_FOR_MANUAL_REVIEW | external=AVAILABLE_UNREVIEWED; stage38=FULLTEXT_AVAILABLE_REVIEW_REQUIRED; audit_A8b=EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED | `FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh` | Map protocol stages, complexity formulas, noise/security assumptions, and PVW-SAB delta to concrete page or section anchors. |
| S41-NATIVE-PERF-INTAKE | WAIT_NATIVE_PERF | external=MISSING; stage37=BLOCKED_EXTERNAL_PERF; audit_A8=BLOCKED_EXTERNAL | `STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh` | Compare cycles, instructions, cache counters, objdump evidence, and Stage 22 specialized/generic timing. |
| S41-EXTERNAL-REGISTRATION | READY_TO_REGISTER | A8=BLOCKED_EXTERNAL; A8b=EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED | `FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf STAGE28_NATIVE_PERF_SUMMARY=/path/to/summary.csv python scripts/register_external_evidence.py` | Registered hashes are intake evidence only; manual interpretation remains required. |
| S41-FINAL-RECHECK | READY_AFTER_UNLOCKS | audit_A9=SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED | `FINAL_RECHECK_CITATION=1 FINAL_RECHECK_PERF=1 FINAL_RECHECK_EXTERNAL_INTAKE=1 bash scripts/run_final_goal_recheck.sh` | A9 may only move beyond scoped-ready after A8/A8b are no longer blocked and claim wording is manually checked. |

## Claim Policy

- `S41-FULLTEXT-INTAKE`: No theorem, algorithm, table, figure, or novelty wording may be upgraded until manual review replaces blocked checklist rows.
- `S41-NATIVE-PERF-INTAKE`: Do not claim theoretical MAT-AVX512 optimality or load/store superiority from current WSL2 proxy evidence.
- `S41-EXTERNAL-REGISTRATION`: Registration alone changes status to review-required, not paper-ready.
- `S41-FINAL-RECHECK`: Keep the final status scoped/review-required until all stronger-claim rows have direct evidence and source review.

## Current Decision

The local engineering evidence chain remains frozen as scoped-ready.
The next meaningful upgrades require external full text and/or
native perf evidence, followed by manual interpretation and a final
goal recheck.
