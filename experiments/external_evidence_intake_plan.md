# External Evidence Intake Plan

Date: 2026-06-25

## Objective

Register external artifacts that can unblock stronger PVW/MAT-SAB claims
without automatically upgrading those claims.

This is needed for two current blockers:

- full 2025/686 text for theorem, algorithm, remark, table, or experiment
  citation checks;
- native Linux or perf-enabled hardware-counter evidence for MAT-AVX512
  load/store attribution.

## Commands

Default missing-evidence registration:

```bash
python scripts/register_external_evidence.py
```

Register local 2025/686 full text:

```bash
FAB686_FULLTEXT_PATH=/path/to/2025-686.pdf \
python scripts/register_external_evidence.py
```

Register a native/perf-enabled Stage 28 summary:

```bash
STAGE28_NATIVE_PERF_SUMMARY=/path/to/stage28_native_perf_counter_gate/summary.csv \
python scripts/register_external_evidence.py
```

## Output

```text
repro/external_evidence_intake/summary.csv
```

The summary records path, SHA-256, size, detected kind, and status.

## Claim Rule

Registered evidence is not a claim upgrade. It changes final audit status to
review-required when appropriate. Manual citation verification or perf
interpretation must still be completed before paper-level wording changes.
