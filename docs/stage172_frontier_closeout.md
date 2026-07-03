# Stage172 Frontier Closeout

Decision: `PASS_STAGE172_FRONTIER_CLOSEOUT_RECORDED`.

Stage172 consolidates the current evidence loop:

- Stage169 is the complete-SAB throughput endpoint.
- Stage170 is component/counter attribution.
- Stage171 is a proof-route boundary for structured compact keygen.

The project can currently claim complete-SAB amortized throughput improvement
for the current exact r=6 PVW/MAT-SAB path on CB5. It cannot claim theoretical
optimality, implemented compact SAB, or paper-level novelty yet.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage172_inputs | PASS | input_stages | stage169_native_repeated_full_sab;stage170_native_split_counters;stage171_structured_compact_feasibility | repro/stage172_frontier_closeout/evidence_inputs.csv | Stage172 consumes Stage169 complete-SAB stats, Stage170 split counters, and Stage171 proof-route status. | Repair missing input before claim refresh. |
| stage172_claim_boundary | PASS | allowed;blocked | 3;3 | repro/stage172_frontier_closeout/claim_matrix.csv | Allowed complete-SAB engineering claim is separated from blocked optimality/compact/paper claims. | Use this matrix when writing reports or deciding next stages. |
| stage172_next_route | PASS | next_engineering_stage | Stage174_from_DFT_locality | repro/stage172_frontier_closeout/next_stage_queue.csv | Near-term automatic work should use a bounded microbench/full-SAB loop, not open-ended proof work. | Run Stage174 unless the user explicitly prioritizes Stage173 proof route. |
| stage172_decision | PASS_STAGE172_FRONTIER_CLOSEOUT_RECORDED | frontier_closeout | recorded | repro/stage172_frontier_closeout/summary.csv | Stage172 closes the Stage169-171 evidence loop and prevents claim drift. | Proceed to Stage174 engineering loop or Stage173 proof loop with explicit scope. |

## Evidence Inputs

| source | path | present | decision |
| --- | --- | --- | --- |
| stage169_native_repeated_full_sab | repro/stage169_cb5_native_repeated_r6_gate/summary.csv | yes | PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE |
| stage170_native_split_counters | repro/stage170_native_split_counter_microbench/summary.csv | yes | PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED |
| stage171_structured_compact_feasibility | repro/stage171_structured_compact_keygen_feasibility/summary.csv | yes | PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY |

## Claim Matrix

| claim | status | evidence | quantitative_value | boundary |
| --- | --- | --- | --- | --- |
| current exact r=6 PVW/MAT-SAB improves complete-SAB amortized throughput on CB5 | ALLOWED_ENGINEERING_CLAIM | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | mean=1.131666667;min=1.115000000;ci95_low=1.095041982 | Metric is T_bootstrap/r versus repeated scalar SAB under spqlios_avx512 on CB5; not all parameters/backends. |
| MAT EP/subdecomp and from_DFT are both material component costs | ALLOWED_ATTRIBUTION | repro/stage170_native_split_counter_microbench/run_metrics.csv | mat_ep_us=66.127151855;from_dft_us=35.211114746 | Component microbench/counter attribution only; not a replacement for full-SAB A/B. |
| from_DFT locality remains a concrete engineering frontier | ALLOWED_NEXT_EXPERIMENT | repro/stage170_native_split_counter_microbench/derived_counter_ratios.csv | cache_miss_rate=0.646958340;ls_fp512=1.919780044 | Needs bounded microbench and full-SAB promotion gate. |
| structured compact could offer larger algorithmic gain | MOTIVATING_UPPER_BOUND_ONLY | repro/stage171_structured_compact_keygen_feasibility/speed_projection.csv | r6_component_upper=1.665316530 | Requires keygen/phase/noise/security/API proof before implementation or paper claim. |
| current MAT AVX512 implementation is theoretically optimal | BLOCKED | repro/stage170_native_split_counter_microbench/derived_counter_ratios.csv;repro/stage171_structured_compact_keygen_feasibility/proof_obligations.csv | not_established | Counters and negative variants do not prove a lower bound. |
| compact/shared-output SAB is implemented and accelerates full SAB | BLOCKED | repro/stage171_structured_compact_keygen_feasibility/proof_obligations.csv | proof_obligations_open=5 | No structured keygen implementation, noise run, or full-SAB benchmark exists. |
| paper-level novelty is established | BLOCKED_LITERATURE_AND_PROOF | repro/stage171_structured_compact_keygen_feasibility/proof_obligations.csv | not_established | Requires real literature matrix, proof status, ablations, and reproducibility package. |

## Frontier

| rank | frontier | why_now | next_gate | risk |
| --- | --- | --- | --- | --- |
| P0 | from_DFT locality and materialization cost | Stage170 shows from_DFT is about 35.21 us/call with high cache-miss and load/store-to-FP512 ratios. | Stage174 bounded from_DFT locality microbench; promote only with full-SAB A/B. | Backend-only wins may not move complete SAB if MAT EP or sparse schedule remains dominant. |
| P1 | structured compact keygen proof route | Stage171 gives an r=6 component upper bound but leaves five proof obligations open. | Stage173 formal equations plus finite/noise toy; no production code before proof. | May require a new security assumption or fail closed-state/API constraints. |
| P2 | full-SAB repeated statistics after any promoted variant | Stage169 is the current complete-SAB endpoint; every new change must return to it. | Native no-perf repeated A/B with T_bootstrap/r, correctness, and resource reporting. | Microbench speedups can disappear at SAB schedule level. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 174 | from_DFT locality experiment | Stage172 selects a concrete non-proof-loop engineering frontier from Stage170 counters. | Design one bounded locality/layout/scratch candidate; require exactness, microbench win, then full-SAB A/B. | If microbench is neutral or full-SAB A/B does not improve, reject/neutral and do not keep tuning blindly. |
| P1 | 173 | structured compact formal phase/noise toy | Only if the project explicitly pursues new keygen/security proof work. | Formal equations plus finite/noise toy checks for compact distribution. | If equations do not close, compact route remains blocked. |
| P2 | 175 | full-SAB claim refresh | After Stage174 or Stage173 produces a promotable variant. | Repeat Stage169-style native full-SAB A/B and update claim matrix. | No complete-SAB claim from microbench-only evidence. |
