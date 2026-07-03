# Stage137 Decompose/DFT Attribution Gate

Date: 2026-07-03

## Decision

`PASS_STAGE137_DFT_CONVERSION_DOMINANT_READY_DFT_ROUTE`

Stage137 splits the Stage134/136 decompose-DFT blocker into decompose-only and DFT-only timing.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage137_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static build for attribution probe. |
| stage137_probe_compile | PASS | gcc_probe_compile | true | Standalone attribution probe compiled. |
| stage137_probe_run | PASS | probe_returncode | 0 | Attribution probe executed. |
| stage137_correctness | PASS | correctness_rows | 6 | Split decompose-only plus DFT-only output matches current full decomp/DFT. |
| stage137_attribution_rows | PASS | bench_rows;attr_rows | 90;6 | Current full, decompose-only, and DFT-only timings recorded. |
| stage137_r4_dft_fraction | RECORDED | min_r4_dft_fraction;max_required_dft_speedup_r4 | 0.862257;1.340453 | DFT fraction and required DFT-only speedup for r=4. |
| stage137_decision | PASS_STAGE137_DFT_CONVERSION_DOMINANT_READY_DFT_ROUTE | promotion_policy |  | Stage137 decides the next decompose/DFT optimization route. |

## Attribution

| backend | r | N | T | Bg_bit | seed | current_full_us | decompose_only_us | dft_only_us | split_total_us | split_over_current | decompose_fraction | dft_fraction | stage135_break_even_target | required_dft_speedup_if_decomp_unchanged | dominant_blocker | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 1024 | 7 | 7 | 0 | 37.129970 | 3.874970 | 34.455430 | 38.330400 | 1.032330 | 0.101094 | 0.898906 | 1.205905 | 1.280150 | DFT_CONVERSION_DOMINANT | DFT_ROUTE_PLAUSIBLE |
| spqlios | 2 | 512 | 7 | 7 | 0 | 15.441800 | 1.815910 | 14.875870 | 16.691780 | 1.080948 | 0.108791 | 0.891209 | 1.714454 | 2.068701 | DFT_CONVERSION_DOMINANT | DFT_ROUTE_HIGH_RISK |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 84.968820 | 11.951150 | 82.787710 | 94.738860 | 1.114984 | 0.126148 | 0.873852 | 1.152711 | 1.340453 | DFT_CONVERSION_DOMINANT | DFT_ROUTE_PLAUSIBLE |
| spqlios | 4 | 512 | 7 | 7 | 0 | 39.583860 | 5.073770 | 31.761250 | 36.835020 | 0.930557 | 0.137743 | 0.862257 | 1.117512 | 1.046580 | DFT_CONVERSION_DOMINANT | DFT_ROUTE_PLAUSIBLE |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 125.489820 | 18.810090 | 111.713260 | 130.523350 | 1.040111 | 0.144113 | 0.855887 | 1.000000 | 1.047184 | DFT_CONVERSION_DOMINANT | DFT_ROUTE_PLAUSIBLE |
| spqlios | 6 | 512 | 7 | 7 | 0 | 49.409580 | 6.450600 | 50.935790 | 57.386390 | 1.161443 | 0.112406 | 0.887594 | 1.000000 | 1.185684 | DFT_CONVERSION_DOMINANT | DFT_ROUTE_PLAUSIBLE |

## Interpretation

If r=4 is DFT-dominant, the next candidate should reduce DFT conversion count or change DFT data layout. If it is mixed, Stage138 must not assume a DFT-only fix is enough.
