# Stage195 Scoped Paper/Repro Refresh

Decision: `PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE`.

Stage195 refreshes the current scoped report package. It is not a completion
claim for the active research goal. It records exactly what can be reported
now, what remains blocked, and how to reproduce the current evidence.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage195_inputs | PASS | required_inputs_present | 1 | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage192_compact_admission_route_selection/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv | Stage195 consumes primary endpoint, manuscript skeleton, compact admission, and local frontier audits. | Repair missing inputs before report use. |
| stage195_claim_ledger | PASS_SCOPED | claims | 5 | repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv | Allowed and denied claims are explicitly separated. | Use only ALLOW_SCOPED wording in reports. |
| stage195_forbidden_claim_scan | PASS | forbidden_hits | 0 | repro/stage195_scoped_paper_repro_refresh/forbidden_claim_scan.csv | Generated report avoids forbidden compact/optimality/novelty phrases. | Fix report before use if nonzero. |
| stage195_decision | PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE | goal_status | active | repro/stage195_scoped_paper_repro_refresh/summary.csv | The scoped package is refreshed; the broader research objective remains active. | Proceed only with new external backend/proof evidence or final citation verification. |

## Final Claim Ledger

| claim | status | safe_wording | quantitative_bound | must_not_say | evidence |
| --- | --- | --- | --- | --- | --- |
| complete_sab_amortized_speedup | ALLOW_SCOPED | The exact full-MAT PVW/MAT-SAB path has recorded complete-SAB T_bootstrap/r speedup over repeated scalar SAB under the recorded platform, backend, parameters, and seeds. | mean 1.131666667x; min 1.115000000x; CI-low 1.095041982x | Do not generalize to all parameters/backends, proof of optimality, or compact/shared-output speedup. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv |
| compact_shared_output_sab | DENY_IMPLEMENTATION_CLAIM | Compact/shared-output MAT-SAB remains a proof-only route with explicit T1/T2/T4 blockers. | production compact permission 0 | Do not say compact/shared-output SAB is implemented or benchmarked at complete-SAB level. | repro/stage192_compact_admission_route_selection/summary.csv |
| exact_addmul_new_code | DENY_CODE_CANDIDATE | Exact addmul has no promoted local code candidate after source/counter/dataflow preflight. | r6 dec-cache full-SAB bound 1.022675x below 3pct gate | Do not claim a new addmul acceleration without measured gates. | repro/stage193_exact_addmul_dataflow_preflight/summary.csv |
| exact_dft_conversion_new_code | DENY_LOCAL_CODE_CANDIDATE | Exact DFT/conversion has no promoted local code candidate; only external backend primitive work remains optional. | torus_to_DFT required component speedup 1.208076492x | Do not reopen direct-scale or component-major batching as complete-SAB acceleration. | repro/stage194_exact_dft_conversion_preflight/summary.csv |
| novelty | SCOPED_ONLY | The current package supports scoped systems/engineering wording only, with related-work comparison still required for final submission. | n/a | Do not assert broad novelty based only on local implementation evidence. | repro/stage177_verified_literature_novelty_gate/literature_matrix.csv |

## Evidence Chain

| item | status | evidence | detail |
| --- | --- | --- | --- |
| primary_endpoint | SUPPORTED_SCOPED | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv | T_bootstrap/r mean 1.131666667x; min 1.115000000x; CI-low 1.095041982x. |
| component_budget | RECORDED | repro/stage180_mat_ep_split_probe/derived_projection.csv | sub 0.103963271;1.389195069; dft 0.169104610;1.208076492; addmul 0.221723249;1.151228774. |
| manuscript_scope | DRAFT_READY_NOT_FINAL | repro/stage188_scoped_manuscript_skeleton/summary.csv | A scoped skeleton exists, but final citation verification remains required. |
| compact_admission | IMPLEMENTATION_DENIED | repro/stage192_compact_admission_route_selection/summary.csv | T1/T2/T4 block compact/shared-output production code. |
| exact_addmul_frontier | NO_CODE_CANDIDATE | repro/stage193_exact_addmul_dataflow_preflight/summary.csv | No addmul candidate passed the complete-SAB projection gate. |
| exact_dft_frontier | NO_LOCAL_CODE_CANDIDATE | repro/stage194_exact_dft_conversion_preflight/summary.csv | No local DFT/conversion candidate passed prior gates and budget checks. |

## Negative Frontier

| frontier | decision | reason | evidence | reopen_condition |
| --- | --- | --- | --- | --- |
| compact_shared_output | PROOF_ONLY | implementation admission denied by T1/T2/T4 gates | repro/stage192_compact_admission_route_selection/summary.csv | T1/T2/T4 proof and then complete-SAB A/B. |
| exact_addmul | NO_CODE | new dec-cache mechanism below 3pct complete-SAB gate; prior families rejected | repro/stage193_exact_addmul_dataflow_preflight/summary.csv | new dataflow reducing selector loads or FMA-equivalent work with counter evidence. |
| exact_dft_conversion | NO_LOCAL_CODE | same-format count closed; backend batching/direct-scale neutral; only external backend primitive possible | repro/stage194_exact_dft_conversion_preflight/summary.csv | new backend primitive with exact equivalence and component speedup above Stage180 gate. |
| paper_package | READY_SCOPED_NOT_FINAL | current evidence can support a scoped engineering report but not final broad claims | repro/stage195_scoped_paper_repro_refresh/scoped_report.md | citation verification and final venue-specific writing pass. |

## Forbidden Claim Scan

| phrase | hits | status | evidence |
| --- | --- | --- | --- |
| theoretically optimal | 0 | PASS | repro/stage195_scoped_paper_repro_refresh/scoped_report.md |
| optimal avx512 | 0 | PASS | repro/stage195_scoped_paper_repro_refresh/scoped_report.md |
| implemented compact | 0 | PASS | repro/stage195_scoped_paper_repro_refresh/scoped_report.md |
| compact sab speedup | 0 | PASS | repro/stage195_scoped_paper_repro_refresh/scoped_report.md |
| novel compact | 0 | PASS | repro/stage195_scoped_paper_repro_refresh/scoped_report.md |
| prove novelty | 0 | PASS | repro/stage195_scoped_paper_repro_refresh/scoped_report.md |
