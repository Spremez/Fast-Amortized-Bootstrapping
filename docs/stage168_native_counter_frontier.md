# Stage168 Native Counter Frontier

Decision: `PASS_STAGE168_ROUTE_TO_NATIVE_REPEATED_AND_SPLIT_COUNTERS`.

Stage168 interprets Stage167 native counters as attribution evidence only. The
full-SAB optimization frontier remains split between:

- current exact-path throughput/statistics, because Stage167 is one perf-wrapped
  run;
- component-level native split counters, because the full run mixes MAT
  external product, decomposition, and materialization;
- structured compact keygen proof, if the research direction wants a new
  algorithm rather than a generic dense-MAT implementation.

Stage160 component shares remain material: MAT+subdecomp share
`0.625878`, and from_DFT materialization share `0.338201`.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage168_inputs | PASS | missing_inputs | none | repro/stage168_native_counter_frontier/evidence_inputs.csv | Stage168 consumes Stage160/163/165/166/167 evidence. | Repair missing input before routing claims. |
| stage168_counter_ratios | PASS | cache_miss_rate;load_store_to_fp512 | 0.367870933;1.592840731 | repro/stage168_native_counter_frontier/derived_counter_ratios.csv | Native counters show both memory/locality and AVX512 arithmetic pressure. | Use split counters before component-level claims. |
| stage168_stats_policy | BLOCKED_STATS | perf_wrapped_speedup | 1.127000000 | repro/stage168_native_counter_frontier/claim_policy.csv | Stage167 has a single perf-wrapped full-SAB run; not enough for final native throughput wording. | Run native no-perf repeated A/B as Stage169. |
| stage168_decision | PASS_STAGE168_ROUTE_TO_NATIVE_REPEATED_AND_SPLIT_COUNTERS | next_stage | Stage169 | repro/stage168_native_counter_frontier/next_stage_queue.csv | Stage168 routes to native repeated full-SAB and split counter gates. | Do not make optimality or final throughput claims before Stage169/170. |

## Evidence Inputs

| source | path | present | decision_or_role |
| --- | --- | --- | --- |
| stage160_component_frontier | repro/stage160_post_fusion_frontier/component_shares.csv | yes | post-fusion component shares |
| stage163_from_dft_batching | repro/stage163_from_dft_batching_microbench/summary.csv | yes | NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED |
| stage165_streaming | repro/stage165_closed_fullmat_streaming_microbench/summary.csv | yes | REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX |
| stage166_compact_algebra | repro/stage166_shared_output_compact_algebra_gate/summary.csv | yes | PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED |
| stage167_native_counters | repro/stage167_cb5_native_r6_counter_refresh/counter_metrics.csv | yes | PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED |

## Derived Counter Ratios

| metric | value | interpretation |
| --- | --- | --- |
| ipc | 1.669427456 | Instructions per cycle for the complete perf-wrapped run. |
| loads_per_cycle | 0.377591580 | High value indicates substantial memory instruction pressure. |
| stores_per_cycle | 0.212563603 | Store pressure remains material after copyback/sub-decomp fusions. |
| fp512_per_cycle | 0.370504829 | AVX512 FP work is material; counters alone do not prove FMA-bound. |
| fp256_per_cycle | 0.069715870 | Residual 256-bit FP work likely comes from FFT/backend paths. |
| load_store_to_fp512_ratio | 1.592840731 | Memory instructions exceed FP512 arithmetic instructions; memory layout remains a plausible frontier. |
| cache_miss_rate | 0.367870933 | High cache miss rate supports locality-focused investigation, but not a standalone optimization claim. |
| branch_miss_rate | 0.004815412 | Branch misses are small relative to memory/FP pressure. |
| perf_wrapped_speedup_vs_scalar_repeated | 1.127000000 | Single perf-wrapped full-SAB run; attribution evidence only, not high-stat performance claim. |
| perf_wrapped_pvw_us | 63578097.000 | Wall-time under perf overhead for current r=6 path. |
| perf_wrapped_scalar_repeated_us | 71628359.000 | Scalar repeated baseline in the same perf-wrapped run. |

## Claim Policy

| claim | status | evidence | limit |
| --- | --- | --- | --- |
| current r=6 exact path has native counter evidence | ALLOWED_ATTRIBUTION | repro/stage167_cb5_native_r6_counter_refresh/counter_metrics.csv | Can discuss cycles/instructions/load/store/cache/FP512 counts for the recorded run. |
| current r=6 exact path is theoretically optimal | BLOCKED | repro/stage167_cb5_native_r6_counter_refresh/counter_metrics.csv; repro/stage166_shared_output_compact_algebra_gate/summary.csv | Counters do not prove a lower bound; generic compact exactness is blocked, but structured keygen remains an open theory route. |
| row-streaming decompose/DFT should replace current tiled AVX | REJECTED | repro/stage165_closed_fullmat_streaming_microbench/summary.csv | Exact but slower; keep current tiled AVX path. |
| component-major from_DFT batching should be integrated | REJECTED_OR_NEUTRAL | repro/stage163_from_dft_batching_microbench/summary.csv | Current backend fused-add remains useful, but batching order is not promoted. |
| generic shared-output compact is drop-in for dense MAT | BLOCKED | repro/stage166_shared_output_compact_algebra_gate/summary.csv | Missing body-to-body cross terms require structured keygen/security/noise proof. |
| native complete-SAB throughput is finalized | BLOCKED_STATS | repro/stage167_cb5_native_r6_counter_refresh/run_metrics.csv | Stage167 is one perf-wrapped run. Need native no-perf repeated A/B and noise/resource gates. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 169 | CB5 native no-perf repeated current r=6 full-SAB gate | Stage167 counters are attribution-only and speedup came from one perf-wrapped run. | Run 3-5 paired native no-perf full-SAB A/B for current r=6 exact path; report T_bootstrap/r mean/min/max/CI plus correctness. | If native repeated speedup is weak or unstable, downgrade final performance wording to WSL/CB5-specific evidence. |
| P1 | 170 | native MAT EP/from_DFT split counter microbench | Stage168 ratios show both FP512 and load/store/cache pressure; Stage160 top shares are MAT+subdecomp and from_DFT. | Measure separate native counters for MAT EP/subdecomp and from_DFT materialization microbench kernels under the current exact path. | If counters cannot isolate components, keep only full-run attribution and do not claim component-level bound. |
| P2 | 171 | structured compact keygen feasibility card | Only if pursuing a new algorithm/key distribution beyond generic dense MAT exactness. | Define algebraic selector constraints, noise equations, security assumption delta, and finite phase/noise toy checks. | If keygen proof is not coherent, compact remains blocked and out of SAB implementation. |
| P3 | 172 | frontier closeout report refresh | After Stage169 or Stage170 supplies stronger native evidence. | Update final report with allowed claims, rejected variants, and remaining proof obligations. | No unsupported paper-level novelty or optimality wording. |
