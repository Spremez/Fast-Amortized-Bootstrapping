# Stage101 CB5 Remote Native Perf Plan

Date: 2026-06-30

## Goal

Resolve CB5 by preserving native Linux hardware-counter evidence for the
complete PVW/MAT-SAB path. The evidence comes from the authorized remote Xeon
platform and complements the earlier WSL-only Stage28/37 blocked probes.

## Inputs

- Remote Stage28 raw logs under `repro/stage101_cb5_remote_native_perf/`.
- Attribution perf logs with retired load/store and AVX512 floating-point
  events.
- Target parameter: `BINARY SET_2_3_2048`, `r=4`, `FFT_LIB=spqlios_avx512`.

## Gates

- Stage28 `hardware_counter_gate` must be `PASS`.
- Complete SAB target-full correctness must be `Pass`.
- Load, store, and AVX512 packed-FP counters must be recorded.
- Speedup must be reported as one-run native evidence only, not as a statistical
  native-performance claim.

## Claim Policy

Stage101 resolves the external platform/counter blocker. It does not prove
MAT-AVX512 theoretical optimality; any optimality claim still needs model,
assembly, and counter interpretation.
