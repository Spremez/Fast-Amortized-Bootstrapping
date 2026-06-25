# Stage 37 Native Perf-Counter Evidence Plan

Date: 2026-06-26

## Goal

Collect or explicitly block native hardware-counter evidence for the
MAT-AVX512 load/store/FMA attribution claim.

Stage 37 does not change scalar SAB or `sab_pvw_*` code. It wraps the Stage 28
perf-counter gate in a reproducible audit that can be rerun on native Linux or
a perf-enabled WSL environment.

## Command

```bash
STAGE37_RUN_BENCH=1 bash scripts/run_stage37_native_perf_counter_audit.sh
```

## Gate

- `perf` must be available in PATH.
- `perf stat` smoke must pass.
- the heavy SAB benchmark must run with `STAGE28_RUN_BENCH=1`;
- the heavy benchmark must report `SAB_PVW_BENCH correctness target_full ... Pass`;
- if the Stage 28 summary reports `PASS`, register it through
  `scripts/register_external_evidence.py` as `STAGE28_NATIVE_PERF_SUMMARY`.

## Failure Handling

- If `perf` is missing or unusable, keep the result as
  `BLOCKED_EXTERNAL_PERF`.
- If the heavy benchmark fails, keep logs and do not upgrade A8.
- If counters are collected, do not call the theoretical-optimality claim
  complete until the counter data is interpreted against Stage 22 timing and
  objdump evidence.

## Artifacts

- `repro/stage37_native_perf_counter_audit/summary.csv`
- `repro/stage37_native_perf_counter_audit/stage28_gate/summary.csv`
- `repro/stage37_native_perf_counter_audit/stage28_gate.log`
- `docs/stage37_native_perf_counter_log.md`
