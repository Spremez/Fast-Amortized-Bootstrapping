# Stage182 Exact Path Negative Frontier

Decision: `PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED`.

Stage182 closes the current exact full-MAT tuning loop after Stage181. The
accepted comparison dimension remains `T_bootstrap/r`: complete SAB time per
processed plaintext lane/bit. The current exact path still has scoped
complete-SAB speedup evidence, but the tested AVX512 sub-decompose route is
negative and cannot be used as an optimization claim.

The important outcome is not "stop all work"; it is stricter routing:

- blind AVX512/layout retuning is closed;
- sub-decompose vectorization is rejected by measurement;
- `torus_to_dft_rows` needs a genuinely new conversion/DFT mechanism;
- `addmul_from_dec_dft` is the only exact component still plausible, but only
  with a new dataflow proof and projected full-SAB impact;
- compact SAB remains a separate proof/literature branch, not implemented
  acceleration.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage182_inputs | PASS | required_inputs_present | 1 | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage180_mat_ep_split_probe/summary.csv; repro/stage181_sub_decomp_avx512_gate/summary.csv | Stage182 consumes complete-SAB endpoint, split probe, and AVX512 sub-decompose gate. | Repair missing inputs before interpreting frontier decisions. |
| stage182_metric_alignment | PASS | primary_endpoint | T_bootstrap/r | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv | All remaining claims are normalized by processed plaintext lane/bit. | Reject raw full-call or kernel-only speedup as final SAB speedup. |
| stage182_sub_decomp_candidate | REJECT | combined_current_speedup | 0.972794296 | repro/stage181_sub_decomp_avx512_gate/comparison.csv | Default-off AVX512 sub-decompose was correct but slower than baseline. | Do not run full-SAB gate for this candidate. |
| stage182_frontier_decision | PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED | route | new_mechanism_required_before_code | repro/stage182_exact_path_negative_frontier/frontier_decisions.csv | Exact full-MAT tuning is closed for blind AVX512/layout retuning; only new dataflow/proof routes remain. | Proceed only to a bounded mechanism screen, not speculative hot-path implementation. |

## Component Recheck

| component | observed_us | share_or_speedup | projection_requirement | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| complete_sab_endpoint | 10465305.389000000 | 1.131666667 | primary endpoint | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv | Accepted comparison dimension is complete SAB time per processed lane. |
| sub_decompose | 10.748525391 | 0.103963271 | 1.389195069 | repro/stage180_mat_ep_split_probe/run_metrics.csv; repro/stage181_sub_decomp_avx512_gate/comparison.csv | Stage181 AVX512 candidate was correct but slower, so this exact route is rejected. |
| torus_to_dft_rows | 17.483339844 | 0.169104610 | 1.208076492 | repro/stage180_mat_ep_split_probe/run_metrics.csv; repro/stage174_from_dft_direct_scale_gate/summary.csv | Share is meaningful, but the tested direct-scale style from_DFT route was neutral. |
| addmul_from_dec_dft | 22.923460937 | 0.221723249 | 1.151228774 | repro/stage180_mat_ep_split_probe/run_metrics.csv; repro/stage165_closed_fullmat_streaming_microbench/summary.csv | Best remaining exact component, but prior layout/streaming retuning is exhausted without a new dataflow mechanism. |
| combined_current | 62.435788086 | 0.819326988 | split coverage sanity | repro/stage180_mat_ep_split_probe/derived_projection.csv | Split probes cover the current hot block well enough for routing, not for final timing claims. |

## Frontier Decisions

| route | decision | best_evidence | quantitative_result | why | reopen_condition |
| --- | --- | --- | --- | --- | --- |
| R1_sub_decompose_avx512 | REJECT | repro/stage181_sub_decomp_avx512_gate/comparison.csv | sub_decompose speedup 0.802790789x; combined_current speedup 0.972794296x | Correct deterministic sinks but slower wall time and projected full-SAB regression. | Only if a different algorithmic decomposition removes work rather than vectorizing the same scalar loop. |
| R2_torus_to_dft_rows | BLOCK_NEW_MECHANISM_REQUIRED | repro/stage180_mat_ep_split_probe/derived_projection.csv; repro/stage174_from_dft_direct_scale_gate/summary.csv | full-SAB share 0.169104610; 3pct requirement 1.208076492x | The share is large enough, but direct-scale/backend locality was already neutral. | A new DFT/conversion mechanism with microbench promotion and full-SAB gate. |
| R3_addmul_from_dec_dft | OPEN_ONLY_FOR_NEW_DATAFLOW_PROOF | repro/stage180_mat_ep_split_probe/derived_projection.csv; repro/stage165_closed_fullmat_streaming_microbench/summary.csv | full-SAB share 0.221723249; 3pct requirement 1.151228774x | This is the only exact component where a modest component gain could matter, but prior tiling/streaming routes failed or were weak. | Assembly/counter-backed dataflow change, not another blind layout retune. |
| R4_exact_same_format_count_reduction | CLOSED | repro/stage178_fullmat_perbit_frontier/component_attribution.csv | 573440 CMUX/MAT EP and from_DFT materialization count remains fixed in exact torus-input API. | Exact same-format API needs coefficient-domain decomposition before each external product. | Closed representation proof that preserves PVW_TMLWE state and noise. |
| R5_structured_compact_sab | BLOCKED_PROOF_AND_LITERATURE | repro/stage176_structured_compact_security_api_gate/summary.csv; repro/stage177_verified_literature_novelty_gate/summary.csv | Potential algorithmic route, not implemented SAB acceleration. | Security/API closure and strong novelty remain unresolved. | Reviewed proof of selector distribution, closed shared-mask accumulator state, and updated literature matrix. |

## Claim Permissions

| claim | permission | allowed_wording | blocked_wording | evidence |
| --- | --- | --- | --- | --- |
| complete_sab_speedup | ALLOW_SCOPED | Current exact PVW/MAT-SAB path has recorded complete-SAB T_bootstrap/r speedup under the measured backend/platform. | Do not claim theoretical optimality or all-parameter speedup. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv |
| avx512_sub_decompose_improvement | DENY | Default-off AVX512 sub-decompose is a negative ablation. | Do not describe it as an optimization or bootstrapping speedup. | repro/stage181_sub_decomp_avx512_gate/comparison.csv |
| mat_external_product_avx512_optimal | DENY | MAT-aware AVX512 exists and has bounded positive/negative evidence. | Do not claim the AVX512 implementation has reached theoretical optimum. | repro/stage182_exact_path_negative_frontier/frontier_decisions.csv |
| new_compact_mat_sab_algorithm | DENY_FOR_IMPLEMENTED_CLAIM | Structured compact remains a proof/literature branch. | Do not call compact SAB implemented or novel from current evidence. | repro/stage176_structured_compact_security_api_gate/summary.csv; repro/stage177_verified_literature_novelty_gate/summary.csv |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 183 | addmul dataflow mechanism screen | Stage182 keeps only R3 as a possible exact-route candidate. | A concrete dataflow must project >=3% complete-SAB T_bootstrap/r improvement before code. | If only layout retuning is proposed, reject without implementation. |
| P1 | 184 | torus_to_DFT new-mechanism gate | A conversion/DFT mechanism beyond direct-scale exists. | Microbench and full-SAB gates must both pass. | Do not reopen Stage174 direct-scale. |
| P2 | 185 | structured compact proof/literature lane | Security/API closure and real related-work review are supplied. | No production SAB code before proof, noise, key distribution, and novelty checks. | Keep compact work out of SAB hot path. |
