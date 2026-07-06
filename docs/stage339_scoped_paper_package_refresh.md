# Stage339 Scoped Paper Package Refresh

Decision: `PASS_STAGE339_SCOPED_PACKAGE_REFRESH_NO_STRONGER_CLAIM`.

The research loop is now at a clean boundary:

- the current supported result is a scoped complete-SAB `T_bootstrap/r` result;
- no new exact implementation mechanism is admitted by Stage338;
- compact/structured SAB remains proof-gated;
- broader parameter and novelty claims require Stage340 evidence.

## Primary Result

| path | parameter | backend | r_body_lanes | samples | pvw_t_bootstrap_over_r_us | scalar_repeated_t_over_r_us | speedup_vs_repeated_scalar | noise_pair_failures | maxrss_kb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_pvw_mat_sab | BINARY SET_2_3_2048 include-zero | spqlios_avx512 WSL | 4 | 10 | 6117083.425 | 10690503.200 | 1.747647 | 0 | 2415796 |

## Next Routes

| priority | route | entry_condition | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage340_parameter_matrix_current_head_refresh | A broader than r=4 SET_2_3_2048 claim is desired. | same-backend complete SAB T_bootstrap/r A/B plus noise/RSS for each parameter and r. | Keep Stage339 claim scoped to the primary row. |
| P1 | stage340_verified_related_work_matrix | Any novelty or paper contribution wording is needed. | real source-checked citations only; no broad shared-mask/common-mask novelty overclaim. | Write as scoped engineering systems result. |
| P2 | stage340_new_mechanism_protocol | A concrete new load/store/count/backend primitive is identified. | mechanism model, isolated equivalence, isolated microbench, then complete SAB A/B. | Reject before hot-path integration. |
| P3 | stage340_formal_compact_state_proof | A neighbor/cross-body closed compact state proof is available. | distribution/keygen/security/noise proof before production code. | Keep compact SAB claim blocked. |
