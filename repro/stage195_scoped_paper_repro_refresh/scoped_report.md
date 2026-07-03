# Scoped PVW/MAT-SAB Report Refresh

Decision: `PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE`.

## Scope

This package reports the current exact full-MAT PVW/MAT-SAB engineering result
using the primary endpoint `T_bootstrap/r`. It does not close the broader
research objective. It also does not authorize compact/shared-output SAB code,
does not claim optimality, and does not upgrade local implementation evidence
into broad novelty.

## Primary Result

Current exact full-MAT PVW/MAT-SAB, under recorded conditions:

- mean `T_bootstrap/r` speedup over repeated scalar SAB:
  `1.131666667x`;
- minimum repeated-run speedup: `1.115000000x`;
- CI lower bound: `1.095041982x`.

## Current Frontiers

| frontier | decision | reason | evidence | reopen_condition |
| --- | --- | --- | --- | --- |
| compact_shared_output | PROOF_ONLY | implementation admission denied by T1/T2/T4 gates | repro/stage192_compact_admission_route_selection/summary.csv | T1/T2/T4 proof and then complete-SAB A/B. |
| exact_addmul | NO_CODE | new dec-cache mechanism below 3pct complete-SAB gate; prior families rejected | repro/stage193_exact_addmul_dataflow_preflight/summary.csv | new dataflow reducing selector loads or FMA-equivalent work with counter evidence. |
| exact_dft_conversion | NO_LOCAL_CODE | same-format count closed; backend batching/direct-scale neutral; only external backend primitive possible | repro/stage194_exact_dft_conversion_preflight/summary.csv | new backend primitive with exact equivalence and component speedup above Stage180 gate. |
| paper_package | READY_SCOPED_NOT_FINAL | current evidence can support a scoped engineering report but not final broad claims | repro/stage195_scoped_paper_repro_refresh/scoped_report.md | citation verification and final venue-specific writing pass. |

## Claim Ledger

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

## Reproduction Entry Points

Use `repro/stage195_scoped_paper_repro_refresh/reproduction_commands.md` for
the current scoped report entry points. Every stronger claim still needs a
new gate with correctness, noise/resource, complete-SAB timing, and citation
verification.
