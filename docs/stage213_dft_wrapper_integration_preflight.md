# Stage213 DFT Wrapper Integration Preflight

Decision: `PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY`.

Stage213 integrates the Stage212 multirow reverse-DFT wrapper behind
`MAT_TRGSW_MULTIROW_DFT_WRAPPER` and compares it against the baseline exact
MAT-EP split probe. This is still not a complete-SAB speedup claim. It is the
gate that decides whether complete-SAB A/B is worth running.

## Correctness

| implementation | r | variant | sample | mismatches | max_gap | status |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 2 | torus_to_dft_rows | 0 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 1 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 2 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 3 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 4 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 5 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 6 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 7 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 8 | 0 | 0 | PASS |
| baseline | 2 | torus_to_dft_rows | 9 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 0 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 1 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 2 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 3 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 4 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 5 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 6 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 7 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 8 | 0 | 0 | PASS |
| baseline | 2 | combined_current | 9 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 0 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 1 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 2 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 3 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 4 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 5 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 6 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 7 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 8 | 0 | 0 | PASS |
| baseline | 4 | torus_to_dft_rows | 9 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 0 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 1 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 2 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 3 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 4 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 5 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 6 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 7 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 8 | 0 | 0 | PASS |
| baseline | 4 | combined_current | 9 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 0 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 1 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 2 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 3 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 4 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 5 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 6 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 7 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 8 | 0 | 0 | PASS |
| wrapper | 2 | torus_to_dft_rows | 9 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 0 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 1 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 2 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 3 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 4 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 5 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 6 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 7 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 8 | 0 | 0 | PASS |
| wrapper | 2 | combined_current | 9 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 0 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 1 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 2 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 3 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 4 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 5 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 6 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 7 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 8 | 0 | 0 | PASS |
| wrapper | 4 | torus_to_dft_rows | 9 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 0 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 1 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 2 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 3 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 4 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 5 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 6 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 7 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 8 | 0 | 0 | PASS |
| wrapper | 4 | combined_current | 9 | 0 | 0 | PASS |

## Aggregate Timing

| implementation | r | variant | samples | mean_per_call_us | min_per_call_us | max_per_call_us |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 2 | combined_current | 10 | 14.697217481 | 12.964086914 | 16.962084961 |
| baseline | 2 | torus_to_dft_rows | 10 | 8.099914844 | 7.374773438 | 9.421129883 |
| baseline | 4 | combined_current | 10 | 32.666125098 | 29.201889648 | 36.092517578 |
| baseline | 4 | torus_to_dft_rows | 10 | 13.686842285 | 12.887816406 | 14.671419922 |
| wrapper | 2 | combined_current | 10 | 15.263959961 | 14.069080078 | 16.809152344 |
| wrapper | 2 | torus_to_dft_rows | 10 | 8.581947168 | 7.607899414 | 9.419084961 |
| wrapper | 4 | combined_current | 10 | 35.525995020 | 32.812876953 | 38.792962891 |
| wrapper | 4 | torus_to_dft_rows | 10 | 14.474955176 | 13.253871094 | 15.835803711 |

## Comparison

| r | variant | baseline_mean_per_call_us | wrapper_mean_per_call_us | speedup_vs_baseline | decision |
| --- | --- | --- | --- | --- | --- |
| 2 | torus_to_dft_rows | 8.099914844 | 8.581947168 | 0.943831823 | NOT_PROMOTED |
| 2 | combined_current | 14.697217481 | 15.263959961 | 0.962870547 | NOT_PROMOTED |
| 4 | torus_to_dft_rows | 13.686842285 | 14.474955176 | 0.945553345 | NOT_PROMOTED |
| 4 | combined_current | 32.666125098 | 35.525995020 | 0.919499231 | NOT_PROMOTED |

## Gates

| gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- |
| G1_stage212_entry | PASS | stage212_proof_present | 1 | repro/stage212_multirow_fft_api_probe/proof_gate.csv | Stage213 starts only after the standalone wrapper probe is promoted. |
| G2_build_compile | PASS | build_rcs;compile_rcs | {'baseline': 0, 'wrapper': 0};{('baseline', 2): 0, ('baseline', 4): 0, ('wrapper', 2): 0, ('wrapper', 4): 0} | repro/stage213_dft_wrapper_integration_preflight | Build and compile baseline and wrapper variants for r=2 and r=4. |
| G3_correctness | PASS | all_mismatches | 0 | repro/stage213_dft_wrapper_integration_preflight/correctness.csv | Each integrated wrapper run must match the row-loop split reference. |
| G4_component_and_combined_timing | PASS_COMPONENT_ONLY | min_dft_rows_speedup;min_combined_speedup | 0.943831823;0.919499231 | repro/stage213_dft_wrapper_integration_preflight/comparison.csv | Full SAB A/B is allowed only if combined_current improves for both r=2 and r=4. |
| G5_stage213_decision | PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY | decision | PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY | repro/stage213_dft_wrapper_integration_preflight/proof_gate.csv | Stage213 decides whether to run complete-SAB A/B for the wrapper path. |

## Next Queue

| priority | route | entry_condition | gate | status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage214_full_sab_ab_dft_wrapper | Stage213 integrated combined_current gate is positive for r=2 and r=4. | Run complete SAB T_bootstrap/r A/B with scalar baseline, current PVW, and wrapper PVW. | not_ready | repro/stage213_dft_wrapper_integration_preflight/proof_gate.csv |
| P1 | native_counter_refresh | Hardware counter attribution is needed before paper-level microarchitectural claims. | Collect load/store/FMA/cycle/cache counters on native Linux. | blocked_locally | repro/stage213_dft_wrapper_integration_preflight/environment.csv |
