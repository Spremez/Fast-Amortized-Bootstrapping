# Stage 41 External Unlock Plan

Date: 2026-06-26

## Goal

Convert the remaining external blockers into executable, auditable gates before
any stronger PVW/MAT-SAB claim is upgraded beyond the current scoped
engineering result.

Stage 41 does not change scalar SAB, the promoted `sab_pvw_*` path, or the
current scoped freeze. It is a claim-upgrade control plane.

## Command

```bash
python scripts/build_stage41_external_unlock_packet.py
```

## Inputs

- `repro/final_goal_completion_audit.csv`
- `repro/stage35_completion_blockers.csv`
- `repro/external_evidence_intake/summary.csv`
- `repro/stage37_native_perf_counter_audit/summary.csv`
- `repro/stage38_fulltext_review_gate/summary.csv`

## Outputs

- `repro/stage41_external_unlock_packet.csv`
- `docs/stage41_external_unlock_packet.md`

## Gates

- Full-text unlock:
  - `FAB686_FULLTEXT_PATH` must point to a recognized PDF/text artifact.
  - Stage 38 must record path, size, and SHA-256.
  - Manual review must map protocol stages, formulas, noise/security
    assumptions, and PVW-SAB deltas to concrete page or section anchors.

- Native perf unlock:
  - Stage 28 must run on native Linux or perf-enabled WSL with
    `STAGE28_RUN_BENCH=1`.
  - `hardware_counter_gate` must be `PASS`.
  - The counters must be interpreted against Stage 22 generic/specialized
    MAT-AVX512 timing and objdump evidence.

- Final recheck unlock:
  - external evidence must be registered through
    `scripts/register_external_evidence.py`;
  - `scripts/run_final_goal_recheck.sh` must be rerun with the selected
    external gates enabled;
  - final audit A9 must be regenerated before any wording changes.

## Failure Handling

- Missing full text keeps theorem-level and novelty claims blocked.
- Missing native perf keeps MAT-AVX512 load/store optimality blocked.
- Registered but unreviewed artifacts change the state to review-required,
  not paper-ready.
- If a gate passes but manual interpretation does not support the stronger
  claim, preserve the negative result and keep the scoped engineering claim.
