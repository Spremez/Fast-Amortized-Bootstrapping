# Stage339 Paper Section Blueprint

## Method Claim

Describe PVW/MAT-SAB as an r-body MAT/RLWE adaptation of the SAB
bootstrapping flow. The implementation claim is for complete SAB throughput per
processed plaintext lane, not for isolated external product speed alone.

## Experimental Endpoint

Primary endpoint: `T_bootstrap/r`.

Primary current-head row:

| parameter | backend | r_body_lanes | samples | pvw_t_bootstrap_over_r_us | scalar_repeated_t_over_r_us | speedup_vs_repeated_scalar | noise_pair_failures | maxrss_kb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BINARY SET_2_3_2048 include-zero | spqlios_avx512 WSL | 4 | 10 | 6117083.425 | 10690503.200 | 1.747647 | 0 | 2415796 |

## Required Caveats

- Current-head main claim is scoped to the primary row.
- Historical r=2 and added-parameter rows need current-head reruns before
  broader wording.
- Negative ablations explain why old exact kernel paths are closed.
- Theoretical optimality, compact SAB, and novelty remain blocked.

## Next Evidence To Add

| priority | route | gate |
| --- | --- | --- |
| P0 | stage340_parameter_matrix_current_head_refresh | same-backend complete SAB T_bootstrap/r A/B plus noise/RSS for each parameter and r. |
| P1 | stage340_verified_related_work_matrix | real source-checked citations only; no broad shared-mask/common-mask novelty overclaim. |
| P2 | stage340_new_mechanism_protocol | mechanism model, isolated equivalence, isolated microbench, then complete SAB A/B. |
| P3 | stage340_formal_compact_state_proof | distribution/keygen/security/noise proof before production code. |
