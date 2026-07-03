# Stage161 Post-Fusion Attribution

Date: 2026-07-03

## Decision

`PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage161_build_run_correctness | PASS | build_rc;run_rc;correctness | 0;0;Pass | Build and run the current r=6 post-fusion explicit path without body-profile overhead. |  |
| stage161_perf_status | missing | perf_available | false | perf not found in WSL | Native counters are required for FMA-vs-memory classification if perf is missing. |
| stage161_objdump_proxy | PASS | fma_family;zmm_refs | 104;494 | Proxy confirms the active rgt4 tiled function contains AVX512/FMA-family instructions, but not throughput optimality. |  |
| stage161_decision | PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED | attribution_scope | proxy_only | Stage161 decides how far current attribution evidence can support the MAT EP frontier. | Proceed to Stage162 and schedule native counter run for current r=6 post-fusion path. |

## Run Metrics

| run_mode | correctness | pvw_lane_avg_us | speedup_vs_scalar_repeated | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- |
| time_fallback_perf_missing | Pass | 6634907.333 | 1.511 | 3577048 | repro/stage161_post_fusion_attribution/run_time.log |

## Perf Status

| perf_available | perf_status | perf_detail | source_log |
| --- | --- | --- | --- |
| false | missing | perf not found in WSL | repro/stage161_post_fusion_attribution/perf_probe.log |

## Instruction Proxy

| metric | count | evidence |
| --- | --- | --- |
| fma_family | 104 | repro/stage161_post_fusion_attribution/objdump_full.txt |
| zmm_refs | 494 | repro/stage161_post_fusion_attribution/objdump_full.txt |
| ymm_refs | 0 | repro/stage161_post_fusion_attribution/objdump_full.txt |
| vmovapd | 144 | repro/stage161_post_fusion_attribution/objdump_full.txt |
| vmovupd | 0 | repro/stage161_post_fusion_attribution/objdump_full.txt |

## Stage160 Linkage

| metric | value | interpretation |
| --- | --- | --- |
| mat_ep_plus_subdecomp | 0.625878 | Dominant fused MAT EP/decompose block; now includes direct diff decomposition under the fusion flag. |
| from_dft_materialization | 0.338201 | Still one materialization per update; reducing count requires representation/schedule change. |
| explicit_sub | 0.000000 | Should be near zero after sub-decompose fusion; this route is now closed. |
| mat_ep_calls;from_dft_calls | 573440;573440 | Stage161 attribution applies to a path with unchanged 573440 MAT EP/materialization calls. |

## Next Queue

| priority | stage | name | reason | gate |
| --- | --- | --- | --- | --- |
| P0 | 162 | materialization-count reduction feasibility | Stage160 from_DFT materialization remains 33.8201% and Stage161 proxy cannot prove MAT EP theoretical optimality. | Prove closure/equivalence before full SAB; reject if materialization count stays 573440. |
| P0 | 161N | native post-fusion counter run | Current WSL perf status is missing; native counters are required to classify FMA vs memory/spill limits. | cycles, instructions, cache, loads/stores, and AVX512 FP counters on current r=6 post-fusion path. |
| P1 | 163 | explicit best-path policy boundary | Stage161 decision is PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED; Stage159 remains an explicit promotion candidate. | No scalar/default behavior change without a separate policy commit. |

Interpretation: the current WSL platform cannot provide perf counters. Stage161 therefore verifies the active AVX512/FMA proxy path and preserves complete-SAB correctness, but does not claim MAT EP theoretical optimality.
