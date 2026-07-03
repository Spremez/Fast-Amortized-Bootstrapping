# Stage134 Generalized Lane-Pair Input EP Gate

Date: 2026-07-03

## Decision

`NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED`

Stage134 replays the generalized lane-pair input compact EP path as the
closure-capable candidate selected by Stage133.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage134_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build for generalized-input replay. |
| stage134_probe_compile | PASS | gcc_probe_compile | true | Standalone generalized lane-pair input EP probe compiled. |
| stage134_probe_run | PASS | probe_returncode | 0 | Generalized lane-pair input EP correctness/microbench probe executed. |
| stage134_correctness | PASS | api_rows | 6 | Lane-pair input/output component, phase, noise, guard, and negative controls pass. |
| stage134_microbench_rows | PASS | bench_rows;ratio_rows | 180;6 | Dense proxy, generalized compact, decomposition, and addmul samples recorded. |
| stage134_full_signal | NEUTRAL_OR_NEGATIVE | min_full_speedup_r4_r6;max_full_speedup_all | 0.910791;1.101122 | Mean dense_all_proxy / generalized compact all-lane timing ratio. |
| stage134_stage130_comparison | RECORDED | min_generalized_over_shared_cost | 1.014795 | Compares closure-capable generalized input against Stage130 shared-source first-step timing. |
| stage134_decision | NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED | promotion_policy |  | Stage134 decides whether generalized lane-pair input EP can enter RGSW/sparse integration. |

## Ratio Results

| r | N | dense all us | generalized all us | full speedup | decomp speedup | addmul speedup | total term ratio | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 41.102100 | 46.537000 | 0.883213 | 0.705037 | 1.092605 | 1.000000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 2 | 512 | 16.928667 | 22.483333 | 0.752943 | 0.748168 | 1.008307 | 1.000000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 1024 | 93.328167 | 102.469300 | 0.910791 | 0.587589 | 1.508816 | 1.250000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 512 | 39.863167 | 42.704133 | 0.933473 | 0.630645 | 1.537896 | 1.250000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 6 | 1024 | 156.724000 | 145.005800 | 1.080812 | 0.556462 | 1.889844 | 1.555556 | POSITIVE_GENERALIZED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 512 | 73.445667 | 66.700767 | 1.101122 | 0.573445 | 1.855769 | 1.555556 | POSITIVE_GENERALIZED_COMPACT_FASTER_THAN_DENSE_PROXY |

## Stage130 Comparison

| r | N | generalized all us | Stage130 shared all us | generalized/shared cost | generalized speedup | Stage130 speedup | decision |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 46.537000 | 45.858533 | 1.014795 | 0.883213 | 0.967843 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 2 | 512 | 22.483333 | 18.647267 | 1.205717 | 0.752943 | 0.990025 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 4 | 1024 | 102.469300 | 85.338133 | 1.200745 | 0.910791 | 1.153336 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 4 | 512 | 42.704133 | 36.185433 | 1.180147 | 0.933473 | 1.281272 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 6 | 1024 | 145.005800 | 117.894967 | 1.229958 | 1.080812 | 1.369582 | CLOSURE_CORRECT_BUT_COSTLY |
| 6 | 512 | 66.700767 | 56.047933 | 1.190066 | 1.101122 | 1.478479 | CLOSURE_CORRECT_BUT_COSTLY |

## Interpretation

Correctness of the closure-capable lane-pair input EP is necessary but
not sufficient. If r=4 remains non-positive, the next aligned work is
decomposition/DFT reuse or streaming for lane-pair input, not RGSW
integration.
