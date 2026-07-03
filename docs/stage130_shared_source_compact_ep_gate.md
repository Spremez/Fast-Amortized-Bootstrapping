# Stage130 Shared-Source Compact EP Gate

Date: 2026-07-03

## Decision

`PASS_STAGE130_SHARED_SOURCE_COMPACT_EP_POSITIVE_PRODUCTION_API_REQUIRED`

Stage130 tests the MAT-RLWE source shape with one shared source/mask and r
body polynomials. It remains outside production headers and `sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage130_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage130_probe_compile | PASS | gcc_probe_compile | true | Standalone shared-source compact EP probe linked against libmosfhet.a. |
| stage130_probe_run | PASS | probe_returncode | 0 | Shared-source compact EP probe executed. |
| stage130_shared_source_correctness | PASS | api_rows | 6 | Shared-source component, phase, noise, and negative-control checks. |
| stage130_microbench_rows | PASS | bench_rows;ratio_rows | 180;6 | Dense-count proxy and shared-source compact samples were recorded. |
| stage130_full_microbench_signal | PASS_POSITIVE | min_full_speedup_r4_r6;max_full_speedup_all | 1.153336;1.478479 | Mean dense_all_proxy / compact_shared_all_lanes timing ratio. |
| stage130_attribution_signal | RECORDED | min_decomp_speedup;min_addmul_speedup | 0.974663;1.052528 | Separate decomposition/DFT and DFT addmul timing attribution. |
| stage130_decision | PASS_STAGE130_SHARED_SOURCE_COMPACT_EP_POSITIVE_PRODUCTION_API_REQUIRED | promotion_policy |  | Stage130 decides only shared-source compact EP production-API readiness. |

## Ratio Summary

| r | N | dense all us | shared compact all us | full speedup | decomp/DFT speedup | addmul speedup | DFT term ratio | total term ratio | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 44.383867 | 45.858533 | 0.967843 | 0.974663 | 1.052528 | 1.125000 | 1.090909 | NEGATIVE_SHARED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 2 | 512 | 18.461267 | 18.647267 | 0.990025 | 1.029681 | 1.112785 | 1.125000 | 1.090909 | NEGATIVE_SHARED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 1024 | 98.423567 | 85.338133 | 1.153336 | 1.001350 | 1.506633 | 1.562500 | 1.428571 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 4 | 512 | 46.363400 | 36.185433 | 1.281272 | 1.022033 | 1.530580 | 1.562500 | 1.428571 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 1024 | 161.466767 | 117.894967 | 1.369582 | 1.002339 | 1.845567 | 2.041667 | 1.806452 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 512 | 82.865700 | 56.047933 | 1.478479 | 1.000692 | 2.020643 | 2.041667 | 1.806452 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |

## Interpretation

This gate directly addresses the Stage129 bottleneck by reducing compact
decomposition/DFT streams from `2r` to `1+r`. Complete SAB acceleration
still requires production API, SAB integration, correctness/noise, and
full `T_bootstrap/r` A/B gates.
