# Stage 42 Closure Verify Plan

Date: 2026-06-26

## Goal

Verify the Stage 42 evidence-closure package without regenerating the Stage 42
audit or its SHA-256 manifest.

This is a read-only consistency gate for the current scoped engineering
evidence chain. It does not change scalar SAB, does not change `sab_pvw_*`,
and does not upgrade blocked novelty, full-text, or native perf claims.

## Commands

No-write check:

```bash
python scripts/verify_stage42_closure.py --check-only
```

Recorded verifier output:

```bash
python scripts/verify_stage42_closure.py --out-dir repro/stage42_closure_verify
```

## Gates

- worktree is clean before verifier output artifacts are written;
- final audit A9 remains
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- Stage 41 external-unlock readiness remains waiting for full text/native perf;
- Stage 42 overall closure is
  `PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED`;
- Stage 42 closure manifest SHA-256 hashes match current files;
- Stage 43 current smoke rows remain `PASS`;
- default and closure-only final recheck summaries contain
  `stage42_evidence_closure=PASS`;
- required Stage42/43 run-log rows are present;
- artifact manifest registers the verifier and closure manifest.

## Outputs

- `repro/stage42_closure_verify/summary.csv`
- `docs/stage42_closure_verify_log.md`

## Failure Handling

Any failed row means the Stage 42 closure package should not be used as
current evidence until the failing artifact is regenerated, restored, or
explicitly re-scoped. Do not delete blocked-claim rows to make the verifier
pass.
