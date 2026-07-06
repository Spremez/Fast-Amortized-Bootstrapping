# Stage338 New Mechanism Or Proof Intake

Decision: `PASS_STAGE338_NO_NEW_MECHANISM_SELECT_SCOPED_PACKAGE_OR_EXTERNAL_PROOF`.

The active goal is still not complete. Current evidence supports a scoped
complete-SAB `T_bootstrap/r` claim, but it does not prove theoretical optimality
for MAT-RLWE SAB and does not admit the compact selector route.

Stage338 therefore fixes the continuation rule:

- implement only after a concrete new load/store/count or backend primitive
  passes an isolated gate;
- reopen compact/structured SAB only after a closed-state proof covers
  neighbor/cross-body selector behavior;
- otherwise proceed with a scoped paper/parameter package using the existing
  complete-SAB evidence and negative ablations.

## Route Decision

| priority | route | entry_condition | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage339_scoped_paper_package_refresh | No new mechanism or formal proof is available. | Produce claim matrix, parameter status, negative ablation table, and repro pack without stronger wording. | Downgrade to engineering note; do not claim optimality. |
| P1 | stage339_new_mechanism_protocol | A concrete new exact mechanism is supplied or derived. | Count model, isolated equivalence, isolated microbench, then full SAB T_bootstrap/r A/B. | Reject before hot-path integration if isolated gate fails. |
| P2 | stage339_formal_compact_state_proof | A neighbor/cross-body closed compact state proof is available. | Distribution/keygen/security/noise proof followed by finite checker and isolated equivalence. | Keep compact route as future work only. |
| P3 | stage339_parameter_matrix_refresh | Paper claim needs more than the current r=4 scoped result. | Run available parameter/r matrix and mark unsupported branches explicitly. | Limit claims to the measured parameter set. |

## Claim Boundary

| claim_or_task | decision | boundary |
| --- | --- | --- |
| scoped_complete_sab_t_bootstrap_over_r | ALLOW | same repo, same backend, r=4 current-head scoped comparison only |
| negative_ablation_table | ALLOW | closed candidates explain why old exact routes should not be repeated |
| theoretical_optimality_of_mat_rlwe_sab | BLOCK | same-format lower bound exists; global optimum is not proven |
| universal_or_multi_parameter_speedup | BLOCK | requires parameter matrix beyond the current scoped result |
| novel_shared_mask_or_common_mask_claim | BLOCK | adjacent fulltext audit blocks broad novelty wording |
