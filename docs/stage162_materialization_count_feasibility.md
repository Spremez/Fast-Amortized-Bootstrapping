# Stage162 Materialization-Count Feasibility

Date: 2026-07-03

## Decision

`PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage162_evidence_inputs | PASS | inputs_present | all | Stage162 consumes Stage160, Stage156, and Stage161 evidence. |  |
| stage162_lower_bound | PASS | reducible_calls_without_rep_change | 0 | Current torus-input API makes observed from_DFT count tight. | Only representation/API changes can reduce call count. |
| stage162_candidate_matrix | PASS | open_routes | backend_batching;representation_change | Separates count reduction from wall-time backend batching. | Do not relabel backend batching as algorithmic count reduction. |
| stage162_decision | PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED | same_format_count_reduction | closed | Stage162 closes unsafe same-format materialization-count reduction. | Proceed to backend batching microbench or representation-changing closure design; do not claim count reduction in same-format path. |

## Lower Bound

| metric | value | interpretation |
| --- | --- | --- |
| observed_from_dft_calls | 573440 | Current post-fusion path materializes every MAT EP output. |
| current_api_lower_bound | 573440 | Under current torus-input MAT EP API, every update output must become torus before the next bit or final extract. |
| mat_ep_calls | 573440 | The lower bound equals observed MAT EP calls; same-format count reduction is not available. |
| reducible_calls_without_representation_change | 0 | Zero under the current exact torus/decomposition API boundary. |

## Candidate Matrix

| candidate | status | mechanism | blocking_evidence | next_action |
| --- | --- | --- | --- | --- |
| persistent_DFT_accumulator | REJECTED_BY_STAGE156 | Keep accumulator in DFT form across CMUX updates. | REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED | Do not reopen without a new exact decomposition/rotation representation. |
| delay_materialization_within_bit | REJECT_COUNT_UNCHANGED | Batch independent same-bit outputs and materialize later. | Each output is still a distinct torus input for the next bit or final extract. | May be recast as batched IFFT backend work, not count reduction. |
| batched_or_vectorized_from_DFT | OPEN_BACKEND_MICROBENCH | Execute multiple materializations with better locality/SIMD/backend batching. | Call count remains 573440; only per-call cost may improve. | Stage163/164 microbench if from_DFT remains above threshold. |
| direct_extract_from_DFT | NOT_MATERIAL | Extract final TLWE directly from DFT accumulator. | Only final boundary could be affected; Stage160 from_DFT is dominated by all CMUX updates, not final extract only. | Do not prioritize before MAT EP/from_DFT bulk path. |
| compact_shared_source_or_decomposed_state | OPEN_REPRESENTATION_CHANGE | Change representation/API so the next operation consumes a closed exact state. | Requires new equivalence/noise gate; not a same-format count reduction. | Design isolated closure/equivalence test before any full-SAB integration. |

## Next Queue

| priority | stage | name | goal | gate |
| --- | --- | --- | --- | --- |
| P0 | 163 | from_DFT backend batching microbench | Measure whether batched/vectorized materialization reduces wall time while preserving the 573440-call semantics. | Promote only if complete SAB improves; label as backend improvement, not algorithmic count reduction. |
| P0 | 164 | compact/decomposed-state closure design | Define a representation-changing exact state that can consume CMUX outputs without torus materialization. | Must pass isolated phase/noise equivalence before any SAB integration. |
| P1 | 161N | native post-fusion counters | Classify the MAT EP+subdecomp block as FMA-bound, memory-bound, or spill-bound on native perf platform. | Current r=6 post-fusion path, not historical r=4 evidence. |
