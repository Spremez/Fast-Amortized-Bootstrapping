# Stage330 High-Stat Reconciliation

Decision: `PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN`.

Stage330 reconciles the existing high-stat direct-DFT evidence with the current
PVW/MAT-SAB claim boundary.  It does not run a new benchmark and it does not
admit compact SAB code.

The primary endpoint remains complete SAB `T_bootstrap/r`: the self-contained
bootstrap time divided by the number of MAT/RLWE body lanes, compared against
running scalar SAB independently for the same number of plaintext bits.

## Summary

| decision | primary_metric | stage296_speedup | stage321_speedup | flag_compatibility | stage296_source_scope | stage321_current_hotcode_scope | paper_current_head_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN | complete_sab_T_bootstrap_over_r_vs_repeated_scalar | 1.735849 | 1.745361 | PASS | historical_hot_code_changed | current_hotcode_equivalent | strict_current_head_10run_still_required_for_exact_paper_table |

## Flag And Metric Compatibility

| check | stage296_perf_direct_dft | stage321_direct_baseline | status |
| --- | --- | --- | --- |
| metric_endpoint | complete SAB T_bootstrap/r | complete SAB T_bootstrap/r | PASS |
| param | SET_2_3_2048 | SET_2_3_2048 | PASS |
| fft_lib | spqlios_avx512 | spqlios_avx512 | PASS |
| r_body_lanes | 4 | 4 | PASS |
| reps | 1 | 1 | PASS |
| include_zero_branch | true | true | PASS |
| ternary_branch | false | false | PASS |
| A_PRNG=none | present | present | PASS |
| ENABLE_VAES=false | present | present | PASS |
| KEY=BINARY | present | present | PASS |
| MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true | present | present | PASS |
| MAT_TRGSW_AVX512_SUB_DECOMP=true | present | present | PASS |
| MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true | present | present | PASS |
| SAB_PVW_BACKEND_FROM_DFT_ADD=true | present | present | PASS |
| SAB_PVW_SUB_DECOMP_FUSION=true | present | present | PASS |
| SAB_PVW_DUAL_SUB_CMUX=true | present | present | PASS |
| SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true | present | present | PASS |

## Source Boundary

| comparison | hot_code_changed | changed_count | changed_paths |
| --- | --- | --- | --- |
| stage296_input_60350e3_to_current_head | yes | 6 | main.c; src/mosfhet/Makefile.def; src/mosfhet/src/fft/spqlios/spqlios-fft-impl-avx512.c; src/mosfhet/src/fft/spqlios/spqlios-fft.h; src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s; src/mosfhet/src/mattrgsw.c |
| stage321_input_e193b30_to_current_head | no | 0 |  |

## Evidence Matrix

| evidence | status | metric | value | scope |
| --- | --- | --- | --- | --- |
| stage296_perf_direct_dft | PASS | complete SAB T_bootstrap/r | speedup=1.735849; T/r=6116156.050us; samples=10 | historical-source high-stat mechanism evidence for direct DFT selected path. |
| stage296_noise_direct_dft | PASS | target final-output pair equivalence/noise | trials=10; pair_failures=0; log2_sigma=-7.759 | historical direct-DFT noise side evidence. |
| stage297_resource_sidecondition | PASS | resource side condition | rss_ratio=1.000005; key_ratio=1.065349 | local resource side condition, not all-parameter memory proof. |
| stage321_direct_baseline | PASS | current-hot-code complete SAB T_bootstrap/r | speedup=1.745361; T/r=6118505.950us; samples=5 | current-hot-code engineering evidence; sample count is 5. |
| stage328_active_goal_audit | OPEN | remaining original-goal gaps | paper_highstat_ready=no; compact=proof_required | stage330 narrows the high-stat gap but does not close optimality or compact proof. |
| stage329_compact_checker | OPEN | compact finite algebra | finite_failures=0; keygen_code_admitted= | compact selector finite algebra passed; no production keygen/security/noise/full-SAB claim. |

## Claim Update

| claim | status | safe_statement | not_supported |
| --- | --- | --- | --- |
| primary_metric_dimension | PASS | The supported PVW/MAT-SAB speedups are amortized complete-SAB T_bootstrap/r against repeated scalar SAB. | Kernel-only speedup or single bootstrap latency as the final algorithm claim. |
| direct_dft_highstat_mechanism | PASS_SCOPED_HISTORICAL_SOURCE | Stage296 gives 10-run direct-DFT evidence with 10 noise trials under the same selected flags and parameter. | It is not by itself an exact current-head paper table because hot-code files changed after 60350e3. |
| current_hotcode_complete_sab | PASS_SCOPED_ENGINEERING | Stage321 direct baseline is current-hot-code equivalent from e193b30 to HEAD and records 5-sample T_bootstrap/r speedup. | Paper-grade current-head >=10 sample claim without a rerun. |
| strict_current_head_paper_ready | PARTIAL_RERUN_REQUIRED | A strict current-head paper table should rerun direct PVW/MAT-SAB with >=10 samples and refreshed noise/resource side conditions. | Claiming the current head has already met the >=10 sample threshold. |
| theoretical_optimality | OPEN | The exact dense implementation frontier is closed under current evidence; theoretical optimality remains unproven. | The MAT/RLWE r-body SAB construction is globally optimal. |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_inputs_present | PASS | Stage296/Stage321 summaries | stage296=True; stage321=True |
| G2_flag_metric_compatibility | PASS | flag rows | all_pass |
| G3_highstat_threshold | PASS | Stage296 samples | 10 |
| G4_current_hotcode_equivalence | PASS | source diff e193b30..HEAD | no_hot_code_diff |
| G5_stage296_source_boundary | BOUNDARY | source diff 60350e3..HEAD | 6 hot-code files changed |
| G6_decision | PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN | claim boundary | high-stat mechanism reconciled; current-head strict high-stat remains optional/required by paper wording |

Generated from input head `318e92e`.
