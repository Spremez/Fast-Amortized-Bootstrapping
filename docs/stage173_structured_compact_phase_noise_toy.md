# Stage173 Structured Compact Phase/Noise Toy

Decision: `PASS_STAGE173_PHASE_NOISE_TOY_PROOF_STILL_OPEN`.

Stage173 is a bounded toy gate for the structured compact route. It checks:

- finite-field phase equivalence between structured dense MAT and compact
  application through a SAB-like CMUX/NCMUX schedule;
- a body-cross negative control that compact must fail to represent;
- a toy variance comparison for omitting logical zero body-cross encryptions.

This does not grant implementation permission. Security reduction and compact
closed-state API remain open.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage173_inputs | PASS | inputs | repro/stage171_structured_compact_keygen_feasibility/proof_obligations.csv;repro/stage175_post_stage174_frontier_refresh/next_stage_queue.csv | repro/stage173_structured_compact_phase_noise_toy/summary.csv | Stage173 consumes Stage171 proof obligations and Stage175 route decision. | Repair missing inputs before interpreting toy results. |
| stage173_phase_toy | PASS | phase_failures | 0 | repro/stage173_structured_compact_phase_noise_toy/finite_phase_results.csv | Structured compact matches structured dense through SAB-like finite CMUX/NCMUX schedule; cross-term negative control mismatches. | If this fails, close or repair compact equations before any code. |
| stage173_noise_toy | PASS | max_compact_over_dense;mean_compact_over_dense | 0.999636957706;0.997953103564 | repro/stage173_structured_compact_phase_noise_toy/noise_toy_results.csv | Toy variance for omitted zero cross terms is no larger than dense zero-padded variance. | Still require real noise proof/simulation before implementation. |
| stage173_implementation_permission | BLOCKED_PROOF | permission_yes | 0 | repro/stage173_structured_compact_phase_noise_toy/proof_status_update.csv | Security reduction and closed-state API are still not proven. | Do not implement compact SAB yet. |
| stage173_decision | PASS_STAGE173_PHASE_NOISE_TOY_PROOF_STILL_OPEN | structured_compact_route | toy_pass_proof_open | repro/stage173_structured_compact_phase_noise_toy/summary.csv | Stage173 advances compact route with finite/toy evidence without granting paper or implementation claims. | Proceed to security/API design or literature gate. |

## Equation Model

| object | equation | meaning |
| --- | --- | --- |
| state | x = (x_0, x_1, ..., x_r) | PVW/MAT-RLWE phase vector: shared component plus r body lanes. |
| structured_selector | M[0,*] arbitrary; M[q,0], M[q,q] arbitrary; M[q,j]=0 for q!=j and q,j>0 | Compact keygen constraint required by Stage171. |
| CMUX_phase | out = addend + M * (rhs - addend) | Finite-field phase model for one SAB CMUX/NCMUX update. |
| compact_apply | out_0=sum_j M[0,j]d_j; out_q=M[q,0]d_0+M[q,q]d_q | Compact external product formula for d=rhs-addend. |
| noise_toy | dense_zero_padded body variance = signal + (1+r)sigma_key^2; compact body variance = signal + 2sigma_key^2 | Toy comparison when omitted cross terms are logical zero encryptions. |

## Phase Toy Sample

| r | trial | field_prime | in_N | r_prec | checked_components | structured_mismatches | negative_cross_mismatches | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 1 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 2 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 3 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 4 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 5 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 6 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 7 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 8 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 9 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 10 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |
| 2 | 11 | 65537 | 16 | 4 | 192 | 0 | 1 | PASS_PHASE_TOY |

Full phase results are in `repro/stage173_structured_compact_phase_noise_toy/finite_phase_results.csv`.

## Noise Toy Sample

| r | trial | input_variance | key_noise_variance | dense_zero_padded_avg_variance | compact_omitted_zero_avg_variance | compact_over_dense | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 1.000000 | 0.010000 | 16.696666666667 | 16.690000000000 | 0.999600718706 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 1 | 1.000000 | 0.010000 | 9.030000000000 | 9.023333333333 | 0.999261720192 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 2 | 1.000000 | 0.010000 | 7.030000000000 | 7.023333333333 | 0.999051683262 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 3 | 1.000000 | 0.010000 | 12.363333333333 | 12.356666666667 | 0.999460771097 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 4 | 1.000000 | 0.010000 | 12.363333333333 | 12.356666666667 | 0.999460771097 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 5 | 1.000000 | 0.010000 | 8.696666666667 | 8.690000000000 | 0.999233422767 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 6 | 1.000000 | 0.010000 | 16.696666666667 | 16.690000000000 | 0.999600718706 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 7 | 1.000000 | 0.010000 | 9.030000000000 | 9.023333333333 | 0.999261720192 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 8 | 1.000000 | 0.010000 | 16.030000000000 | 16.023333333333 | 0.999584113121 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 9 | 1.000000 | 0.010000 | 8.030000000000 | 8.023333333333 | 0.999169779992 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 10 | 1.000000 | 0.010000 | 7.030000000000 | 7.023333333333 | 0.999051683262 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |
| 2 | 11 | 1.000000 | 0.010000 | 12.696666666667 | 12.690000000000 | 0.999474927803 | PASS_NOISE_TOY_COMPACT_LE_DENSE_ZERO_PADDED |

Full noise results are in `repro/stage173_structured_compact_phase_noise_toy/noise_toy_results.csv`.

## Proof Status

| obligation | stage173_status | remaining_gap | implementation_permission |
| --- | --- | --- | --- |
| keygen_distribution | PARTIAL_TOY_EQUATIONS_DEFINED | Need formal distribution/hybrid argument for omitted zero encryptions. | NO |
| phase_invariant | TOY_PASS | Finite-field schedule toy is not a formal polynomial/RLWE proof. | NO |
| noise_accounting | TOY_PASS | Toy variance ignores correlations, modulus effects, and real bootstrapping-key noise. | NO |
| security_reduction | OPEN | Need real reduction or explicit structured assumption before novelty claim. | NO |
| closed_state_API | TOY_PHASE_CLOSED_PVW_VECTOR | Need API design proving compact key material can feed SAB without dense re-expansion. | NO |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 176 | structured compact security/API design card | Stage173 finite phase/noise toy passes but implementation permission remains NO. | Define keygen distribution, security assumption/reduction, and closed-state API without dense re-expansion. | If security/API cannot close, compact remains a theoretical upper-bound route only. |
| P1 | 177 | literature matrix refresh | Before any structured compact novelty claim. | Verify real related work for compact/multi-output/PVW/MAT bootstrapping. | No novelty wording without verified sources. |
