# Stage164 Representation Closure Route

Decision: `PASS_STAGE164_REPRESENTATION_ROUTE_TO_CLOSED_FULL_MAT_STREAMING_GATE`.

Stage164 closes the immediate post-Stage163 routing question. The current code
does not have a ready representation-changing path that both reduces
materialization count and preserves the PVW shared-mask accumulator invariant.
The next executable route is a closed full-MAT decompose/DFT streaming
microbench, not SAB production integration.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage164_evidence_inputs | PASS | missing_sources | none | repro/stage164_representation_closure_route/evidence_inputs.csv | Stage164 consumes the compact closure, lazy DFT, post-fusion profile, materialization count, and backend batching gates. | Repair missing evidence before routing representation work. |
| stage164_dimension_model | PASS | generic_exact_selector_lower_bound | (1+r)^2 per gadget level | repro/stage164_representation_closure_route/dimension_model.csv | A generic exact MAT selector is a full linear map; compact term reduction needs a structured keygen proof. | Do not claim compact exactness from isolated lane-local kernels. |
| stage164_candidate_matrix | PASS | selected_candidate | closed_full_mat_kernel_and_decompose_dft | repro/stage164_representation_closure_route/candidate_matrix.csv | Closed routes and open high-risk routes are separated from the next executable route. | Run Stage165 closed full-MAT streaming/decompose-DFT microbench. |
| stage164_decision | PASS_STAGE164_REPRESENTATION_ROUTE_TO_CLOSED_FULL_MAT_STREAMING_GATE | next_executable_stage | Stage165 | repro/stage164_representation_closure_route/next_stage_queue.csv | Stage164 prevents another theory loop by selecting a concrete microbench before production changes. | Implement Stage165 as an isolated exact-output kernel gate. |

## Evidence Inputs

| source | path | present | decision |
| --- | --- | --- | --- |
| stage139 | repro/stage139_compact_closure_audit/summary.csv | yes | PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE |
| stage156 | repro/stage156_lazy_dft_closure_gate/summary.csv | yes | REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED |
| stage160 | repro/stage160_post_fusion_frontier/summary.csv | yes | PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED |
| stage162 | repro/stage162_materialization_count_feasibility/summary.csv | yes | PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED |
| stage163 | repro/stage163_from_dft_batching_microbench/summary.csv | yes | NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED |

## Candidate Matrix

| candidate | status | blocking_evidence | mechanism_tested | research_action |
| --- | --- | --- | --- | --- |
| same_format_materialization_count_reduction | CLOSED | PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED | Reduce from_DFT calls without changing torus-input accumulator/API. | Do not reopen unless the accumulator representation changes. |
| from_dft_backend_batching | NEUTRAL_NOT_PROMOTED | NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED | Use component-major batching to lower per-call materialization wall time. | Keep existing fused-add backend; do not integrate batching. |
| naive_lazy_dft_accumulator | REJECTED | REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED | Keep only DFT accumulator outputs across CMUX steps. | Rejected because the next MAT EP needs nonlinear coefficient-domain decomposition. |
| diagonal_compact_direct_sab_state | REJECTED | PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE | Insert compact diagonal/lane-local output directly as a PVW_TMLWE SAB accumulator. | Rejected because lane-specific masks violate the shared-mask PVW invariant. |
| closed_full_mat_kernel_and_decompose_dft | VALID_CURRENT_EXECUTABLE_ROUTE | Stage160 dominant component remains mat_ep_plus_subdecomp; Stage140 lower bound keeps closed full-MAT as valid state. | Preserve PVW_TMLWE state and optimize decompose/DFT/addmul constant factors. | Run a closed full-MAT streaming/decompose-DFT microbench before production changes. |
| structured_shared_output_compact_keygen | OPEN_THEORY_KEYGEN_REQUIRED | Generic dense selector exactness needs (1+r)^2 terms per level; fewer terms require a new structured key distribution/proof. | Design compact selector rows that output one shared mask plus r bodies. | Only proceed after an algebra/keygen/noise proof gate; no production SAB integration yet. |

## Dimension Model

| r | pvw_state_polys | generic_dense_selector_terms_per_level | diagonal_compact_masks | generic_exact_term_lower_bound | interpretation |
| --- | --- | --- | --- | --- | --- |
| 2 | 3 | 9 | 2 | 9 | A generic encrypted MAT selector is a full linear map from 1+r decomposed input rows to 1+r output polynomials. |
| 4 | 5 | 25 | 4 | 25 | A generic encrypted MAT selector is a full linear map from 1+r decomposed input rows to 1+r output polynomials. |
| 6 | 7 | 49 | 6 | 49 | A generic encrypted MAT selector is a full linear map from 1+r decomposed input rows to 1+r output polynomials. |
| 8 | 9 | 81 | 8 | 81 | A generic encrypted MAT selector is a full linear map from 1+r decomposed input rows to 1+r output polynomials. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 165 | closed full-MAT decompose/DFT streaming microbench | Stage164 selects valid current-state executable route. | Compare current all-row dec_dft plus MAT-aware AVX addmul against row-streamed dec_dft/addmul without losing exact DFT output. | If streaming loses to current tiled AVX, close this route and keep current full-MAT kernel. |
| P1 | 166 | shared-output compact algebra/keygen proof gate | Only if pursuing count/key-size reduction beyond full-MAT constant factors. | Prove a compact selector can produce one shared mask and r bodies with acceptable noise/security. | If generic dense exactness or noise proof fails, do not integrate compact SAB. |
| P2 | 167 | native current r=6 counter refresh | Native Linux perf host available. | Measure current post-fusion r=6 retired loads/stores/FMA/cycles for MAT EP and from_DFT attribution. | If only WSL proxy is available, keep optimality claims blocked. |
