# Stage136 Batched Decompose/DFT Gate

Date: 2026-07-03

## Decision

`NEUTRAL_STAGE136_BATCHED_DECOMP_DFT_MISSES_TARGET`

Stage136 tests the first concrete decompose/DFT optimization candidate
after Stage135 quantified the target.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage136_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static library build for batched decompose/DFT probe. |
| stage136_probe_compile | PASS | gcc_probe_compile | true | Standalone batched decompose/DFT probe compiled. |
| stage136_probe_run | PASS | probe_returncode | 0 | Batched decompose/DFT correctness and microbench probe executed. |
| stage136_correctness | PASS | correctness_rows | 6 | Batched decomposition exactly matches decompose_i and DFT output. |
| stage136_microbench_rows | PASS | bench_rows;ratio_rows | 60;6 | Current and batched decompose/DFT timings recorded. |
| stage136_r4_target | NEUTRAL_OR_NEGATIVE | min_r4_speedup | 0.671246 | Stage136 must meet Stage135 r=4 break-even targets to proceed. |
| stage136_decision | NEUTRAL_STAGE136_BATCHED_DECOMP_DFT_MISSES_TARGET | promotion_policy |  | Stage136 decides whether batched decompose/DFT is enough for full EP rebench. |

## Ratio Results

| backend | r | N | T | Bg_bit | seed | current_mean_us | batched_mean_us | speedup_current_over_batched | stage135_break_even_target | stage135_5pct_target | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 1024 | 7 | 7 | 0 | 37.081120 | 53.432470 | 0.693981 | 1.205905 | 1.302486 | MISSES_STAGE135_TARGET |
| spqlios | 2 | 512 | 7 | 7 | 0 | 16.275470 | 24.533180 | 0.663406 | 1.714454 | 1.912783 | MISSES_STAGE135_TARGET |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 79.256410 | 107.128340 | 0.739827 | 1.152711 | 1.245156 | MISSES_STAGE135_TARGET |
| spqlios | 4 | 512 | 7 | 7 | 0 | 31.795230 | 47.367460 | 0.671246 | 1.117512 | 1.212734 | MISSES_STAGE135_TARGET |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 104.790060 | 146.828530 | 0.713690 | 1.000000 | 1.000000 | MISSES_STAGE135_TARGET |
| spqlios | 6 | 512 | 7 | 7 | 0 | 51.947400 | 73.886750 | 0.703068 | 1.000000 | 1.000000 | MISSES_STAGE135_TARGET |

## Interpretation

This candidate preserves correctness. If it misses the r=4 target, the
bottleneck is likely DFT conversion count or memory traffic rather than
only the `decompose_i` loop overhead.
