# Stage225 Exact Refresh Noise/Resource Rerun

Decision: `PASS_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE`.

Stage225 reruns fresh correctness/noise and resource gates for the exact closed
dense MAT/PVW backend path measured in Stage224. This closes the gap where
Stage224 used inherited Stage148 side conditions.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage225_exact_refresh_noise_resource_rerun/input_status.csv | Stage225 consumes Stage224 performance and reruns fresh side conditions. |
| G2_stage224_admission | PASS | stage225_selected | true | repro/stage224_exact_pvw_mat_avx_resource_refresh/next_stage_queue.csv | Fresh side-condition rerun is valid only after Stage224 positive performance refresh. |
| G3_fresh_noise | PASS | seeds;failures;avg_gap | 3;0/0/0;-0.097333 | repro/stage225_exact_refresh_noise_resource_rerun/noise_results.csv; repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv | Fresh final-output noise/correctness for the Stage224 backend path. |
| G4_fresh_resource | PASS | key_bytes_ratio;vmhwm_ratio;time_max_rss_ratio | 1.122537;1.031111;1.030965 | repro/stage225_exact_refresh_noise_resource_rerun/resource_results.csv; repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv | Fresh key/memory side conditions for the Stage224 backend path. |
| G5_claim_boundary | PASS_ENGINEERING_SIDE_CONDITIONS_ONLY | claim_boundary | no_compact_complete_sab_claim;no_theoretical_optimality | docs/stage225_exact_refresh_noise_resource_rerun.md | Stage225 strengthens exact-route evidence only; it does not change algorithmic novelty claims. |
| G6_stage225_decision | PASS_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE | decision | PASS_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE | repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv | Fresh side conditions are ready for Stage226 claim/counter package if gates pass. |

## Noise Aggregate

| r | seeds | points | pvw_failures | scalar_failures | pair_failures | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | avg_pvw_minus_scalar_log2 | stage148_avg_pvw_minus_scalar_log2 | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 3 | 36864 | 0 | 0 | 0 | -0.416 | 0.084 | -0.097333 | 0.176333 | PASS |

## Noise Runs

| r | seed | status | points | pvw_failures | scalar_failures | pair_failures | pvw_log2_sigma_torus | scalar_log2_sigma_torus | pair_log2_sigma_torus | pvw_minus_scalar_log2 | max_allowed_log2_gap | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 6869580 | Pass | 12288 | 0 | 0 | 0 | -8.372 | -7.957 | -7.617 | -0.416 | 4.000 | repro/stage225_exact_refresh_noise_resource_rerun/noise_backend_seed_6869580.log |
| 6 | 6869581 | Pass | 12288 | 0 | 0 | 0 | -8.270 | -8.310 | -7.808 | 0.040 | 4.000 | repro/stage225_exact_refresh_noise_resource_rerun/noise_backend_seed_6869581.log |
| 6 | 6869582 | Pass | 12288 | 0 | 0 | 0 | -8.218 | -8.302 | -7.710 | 0.084 | 4.000 | repro/stage225_exact_refresh_noise_resource_rerun/noise_backend_seed_6869582.log |

## Resource Comparison

| runs | pvw_key_bytes | scalar_key_bytes | key_bytes_ratio | stage148_key_bytes_ratio | pvw_keygen_lane_avg_us | scalar_keygen_lane_avg_us | keygen_lane_ratio | pvw_vmhwm_kb | scalar_vmhwm_kb | vmhwm_ratio | stage148_vmhwm_ratio | pvw_time_max_rss_kb | scalar_time_max_rss_kb | time_max_rss_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1032871032 | 920121648 | 1.122537 | 1.122537 | 748776.500 | 632231.667 | 1.184339 | 1191672.000 | 1155716.000 | 1.031111 | 1.030966 | 1191808.000 | 1156012.000 | 1.030965 | PASS |

## Resource Runs

| run | mode | status | keygen_us | keygen_lane_avg_us | estimated_key_bytes | estimated_key_bytes_ratio_vs_scalar_repeated | internal_vmhwm_kb | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | pvw | PASS | 4492659 | 748776.500 | 1032871032 | 1.122537 | 1191672 | 1191808 | repro/stage225_exact_refresh_noise_resource_rerun/resource_pvw_run_0.log |
| 0 | scalar | PASS | 3793390 | 632231.667 | 920121648 | 1.000000 | 1155716 | 1156012 | repro/stage225_exact_refresh_noise_resource_rerun/resource_scalar_run_0.log |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage226_exact_mat_avx_counter_attribution | Stage224 performance and Stage225 fresh side conditions pass. | Attribute backend-vs-wrapper gain to cycles/load/store/FMA where counters are available. | selected | Keep timing-only exact-route evidence and do not claim backend mechanism. | repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv |
| P1 | paper_claim_boundary_update | After Stage226 counter attribution or if counters remain unavailable. | Separate exact MAT/PVW engineering acceleration from blocked compact route. | future | No novelty/optimality claim. | theory_checks/stage150_claim_scope_model.md |
| P2 | neighbor_capable_compact_state_proof | Only if user chooses a new compact algebra/proof branch. | Define closed neighbor-capable compact state before implementation. | proof_only_deferred | Do not touch SAB hot path. | repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv |
