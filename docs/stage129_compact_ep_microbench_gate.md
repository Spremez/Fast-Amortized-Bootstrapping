# Stage129 Compact EP Microbench Gate

Date: 2026-07-03

## Decision

`NEUTRAL_STAGE129_COMPACT_EP_MICROBENCH_NOT_PROMOTED`

Stage129 benchmarks the Stage128 API-shaped compact EP kernel in isolation
against a dense-count proxy. It remains outside production headers and
`sab_pvw_*`.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage129_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build using FFT_LIB=spqlios. |
| stage129_probe_compile | PASS | gcc_probe_compile | true | Standalone compact EP microbench probe linked against libmosfhet.a. |
| stage129_probe_run | PASS | probe_returncode | 0 | Compact EP microbench probe executed. |
| stage129_api_correctness_guard | PASS | api_rows | 6 | Stage128 API correctness gate is replayed before timing. |
| stage129_microbench_rows | PASS | bench_rows;ratio_rows | 180;6 | Dense-count proxy and compact all-lane samples were recorded. |
| stage129_full_microbench_signal | NEUTRAL_OR_NEGATIVE | min_full_speedup_r4_r6;max_full_speedup_all | 0.888032;1.109918 | Mean dense_all_proxy / compact_all_lanes timing ratio. |
| stage129_attribution_signal | RECORDED | min_decomp_speedup;min_addmul_speedup | 0.580632;0.891968 | Separate decomposition/DFT and DFT addmul timing attribution. |
| stage129_decision | NEUTRAL_STAGE129_COMPACT_EP_MICROBENCH_NOT_PROMOTED | promotion_policy |  | Stage129 decides only isolated microbench promotion readiness. |

## Ratio Summary

| r | N | dense all us | compact all us | full speedup | decomp/DFT speedup | addmul speedup | DFT term ratio | total term ratio | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 43.514000 | 55.423500 | 0.785118 | 0.731624 | 0.891968 | 1.125000 | 1.000000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 2 | 512 | 19.101600 | 23.130367 | 0.825823 | 0.747152 | 1.009838 | 1.125000 | 1.000000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 1024 | 92.304300 | 103.942533 | 0.888032 | 0.615331 | 1.369610 | 1.562500 | 1.250000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 512 | 44.274367 | 47.828667 | 0.925687 | 0.619392 | 1.488801 | 1.562500 | 1.250000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 6 | 1024 | 214.858233 | 193.580300 | 1.109918 | 0.580632 | 1.796338 | 2.041667 | 1.555556 | POSITIVE_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 512 | 77.767733 | 73.112533 | 1.063672 | 0.588463 | 1.867126 | 2.041667 | 1.555556 | POSITIVE_COMPACT_FASTER_THAN_DENSE_PROXY |

## Interpretation

The benchmark endpoint is all r compact lanes versus a dense-count proxy.
The valid downstream use is production API or kernel design only if the
microbench signal is positive. Complete SAB acceleration still requires
later full `T_bootstrap/r` A/B, correctness, noise, and resource gates.
