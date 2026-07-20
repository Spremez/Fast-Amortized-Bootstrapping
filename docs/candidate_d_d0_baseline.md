# Candidate D D0 Baseline Freeze

Decision: `PASS_D0_CANDIDATE_D_BASELINES_FROZEN`.

## Primary Metric

The primary metric is exactly `T_complete_bootstrap/(r*N_active)` in `us`.
For this frozen row, `N_active=2048`. Historical WSL high-stat
values remain frozen source evidence, but they are not formal native-Linux
performance. Newly executed WSL commands are correctness/smoke evidence only.

## Target Parameters

`in_N=2048`, `out_N=2048`,
`out_k=1`, `l=1`,
`bg_bit=23`, `prec=3`, `h=39`,
`r_prec=7`, `sigma_out=2^-50`, and
`H=(h+1)*r_prec*in_N=573440`.

## Frozen Baselines

| baseline | status | T_complete_bootstrap (us) | T/r (us) | T/(r*N_active) (us) |
| --- | --- | ---: | ---: | ---: |
| B0a repeated scalar | FROZEN_HISTORICAL_HIGHSTAT | 42762012.800 | 10690503.200 | 5219.972265625 |
| B0b independent-mask shared-output-key control | REQUIRED_NOT_YET_LOCAL |  |  |  |
| B1 exact-dense PVW/MAT-SAB | FROZEN_HISTORICAL_HIGHSTAT | 24468333.700 | 6117083.425 | 2986.857141113 |
| B2 relevant local BatchBoot composition | REQUIRED_NOT_YET_LOCAL |  |  |  |

B1 uses `r=4`, has speedup `1.747647` versus B0a, and has pair failures
`0/10`. B0b and B2 are required but not yet local; neither is measured here.

## WSL Smoke Disposition

The D0 WSL smoke attempt is `ENVIRONMENT_BLOCKED`. It was interrupted after
writing tracked Stage 33 output, so it produced
`NO_VALID_ISOLATED_SMOKE_RESULT`. The two affected Stage 33 files were
restored and verified against their exact `1164b3f` Git blob identities.
No smoke timing is used as performance evidence.

## Immutable Anchors

- `repro/candidate_a_star_cycle_gate/summary.csv` `c7a003c39d8e56f1cc4ca0845cffe7e68f81cd41a8979d661f8a3df525a96d09` (candidate_a_terminal_decision)
- `repro/candidate_b_factorized_gate/summary.csv` `c758785b0ce7d4d6ef56bb44639b381780ef0d529dc17c8f2544ec67ce3b7a91` (candidate_b_terminal_decision)
- `repro/candidate_c_rank_bounded_gate/terminal_record.csv` `7c7e60bd9a201d4ed943d411dbd40be76ece8f4942822ca31ed278d53c8863d7` (candidate_c_terminal_decision)
- `repro/stage331_current_head_highstat_refresh/summary.csv` `23d3c2611329f189a88f6bdc645e9ed1ac237d19159e79401d2fc11b9c03ad56` (b0a_b1_highstat_metrics)
- `repro/stage345_binary_matrix_synthesis/binary_matrix.csv` `97014b127ad5061dc10fbd3cb3ab53fb06d9ebc69b436011760778425208ea9b` (b1_backend_and_metric_cross_check)
- `src/sab_pvw.c` `6aaabf61f010e0154b826855286137afc39de9b2520ee09e2ca43d5accf5e2ac` (b1_exact_dense_pvw_sab_source)
- `src/mosfhet/src/mattrgsw.c` `5da51089a748f7f1f54b56f81c2948ced14f0be4dd431bcffb2339af97c527fa` (b1_mat_trgsw_source)
- `main.c` `d402980a203aacbaf6b281a9f7245cf14b72c2c80468e5a05050f35373eb11f8` (target_parameters_and_smoke_harness)
