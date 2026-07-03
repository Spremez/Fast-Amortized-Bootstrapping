# Stage169 Validation Plan

Goal: upgrade CB5 performance evidence from Stage167's single perf-wrapped run
to native no-perf repeated complete-SAB A/B.

Protocol:

- backend: `spqlios_avx512`;
- parameter: `BINARY SET_2_3_2048`;
- explicit path: active-buffer, backend FromDFT-add, sub-decompose fusion,
  r>4 tiled AVX512 MAT EP;
- runs: `3` no-perf executions of `./main`;
- primary endpoint: `T_bootstrap/r`, reported as PVW lane time versus repeated
  scalar lane time.

Passing requires correctness for every sample and stable speedup statistics.
