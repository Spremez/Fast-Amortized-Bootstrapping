# Stage 61 Native Perf Unlock Probe Log

Date: 2026-06-26

## Purpose

Stage 61 reruns the native perf-counter unlock command from Stage52 on the
current WSL/Linux platform. This stage tests whether MAT-AVX512 hardware-counter
attribution can be unlocked; it does not run a performance benchmark when
`perf` is missing and it does not upgrade theoretical load/store/FMA claims.

## Command

```bash
STAGE28_PERF_GATE_OUT_DIR=repro/stage61_native_perf_unlock_probe \
STAGE28_RUN_BENCH=1 \
bash scripts/run_stage28_native_perf_counter_gate.sh
```

## Result

```text
environment = RECORDED
perf_command = MISSING
hardware_counter_gate = BLOCKED
```

The current WSL2 environment still has no `perf` command in `PATH`. Therefore
Stage61 does not unlock native hardware-counter evidence, and the MAT-AVX512
theoretical load/store/FMA attribution claim remains blocked.

## Evidence

- `repro/stage61_native_perf_unlock_probe/summary.csv`
- `repro/stage61_native_perf_unlock_probe/environment.log`
- `repro/stage61_native_perf_unlock_probe/perf_smoke.log`
