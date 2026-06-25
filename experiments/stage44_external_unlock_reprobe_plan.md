# Stage 44 External Unlock Re-probe Plan

Date: 2026-06-26

## Goal

Refresh the two remaining external-unlock conditions after the Stage 42/43
closure package:

- 2025/686 direct full-text availability for theorem-level protocol and
  novelty review;
- native Linux or perf-enabled WSL hardware-counter availability for
  MAT-AVX512 load/store attribution.

This stage is not a new SAB optimization, benchmark, or claim upgrade. It only
records whether stronger claims can proceed beyond the current scoped
engineering boundary.

## Command

```bash
bash scripts/run_stage44_external_unlock_reprobe.sh
```

Optional environment variables:

```bash
STAGE44_OUT_DIR=repro/stage44_external_unlock_reprobe
STAGE44_RUN_NATIVE_BENCH=1
FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf
STAGE28_NATIVE_PERF_SUMMARY=/path/to/native/stage28/summary.csv
```

## Gates

- Citation probe must run and write `citation_probe/summary.csv`.
- Native perf probe must run and write `native_perf_gate/summary.csv`.
- `stage44_decision` stays `WAIT_EXTERNAL_UNLOCKS` unless direct full text or
  hardware-counter evidence becomes available.
- Any available full text remains `AVAILABLE_UNREVIEWED` until manual
  theorem/algorithm/citation review gives concrete source anchors.
- Any hardware-counter PASS remains interpretation-required until it is mapped
  back to the Stage 22 MAT-AVX512 model.

## Failure Handling

- If network access is blocked, preserve the HTTP/Cloudflare/403 evidence.
- If `perf` is missing or unusable, preserve the blocker and do not infer
  anything negative about the MAT kernel.
- Do not update final claim labels from this stage alone.
