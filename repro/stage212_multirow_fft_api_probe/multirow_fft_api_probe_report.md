# Stage212 Multirow FFT API Probe

Decision: `PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213`.

Stage212 tests the narrowest executable continuation admitted by Stage211: a
standalone multirow reverse-DFT API wrapper for the current SPQLIOS primitive.
The probe does not modify `sab_pvw_*` or the scalar SAB path. It compares the
current `execute_reverse_torus64` row loop against two exact wrapper shapes:
interleaved per-row scratch and two-phase convert/ifft/copy scratch.

Promotion is deliberately strict: both the 3-row case, corresponding to
MAT rows for r=2 when k=1 and T=1, and the 5-row case, corresponding to r=4,
must pass exact correctness and reach at least `1.03x`
component speedup before any SAB integration preflight is allowed.

## Correctness

| rows | variant | mismatches | max_abs_diff | status | evidence |
| --- | --- | --- | --- | --- | --- |
| 3 | multirow_interleaved_scratch | 0 | 0 | PASS | repro/stage212_multirow_fft_api_probe/run_probe.log |
| 3 | multirow_two_phase_scratch | 0 | 0 | PASS | repro/stage212_multirow_fft_api_probe/run_probe.log |
| 5 | multirow_interleaved_scratch | 0 | 0 | PASS | repro/stage212_multirow_fft_api_probe/run_probe.log |
| 5 | multirow_two_phase_scratch | 0 | 0 | PASS | repro/stage212_multirow_fft_api_probe/run_probe.log |

## Aggregate Timing

| rows | variant | samples | mean_per_group_us | min_per_group_us | max_per_group_us | mean_per_row_us |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | current_execute_loop | 10 | 12.136842481 | 9.194924805 | 14.096119141 | 4.045614160 |
| 3 | multirow_interleaved_scratch | 10 | 9.858934668 | 8.335997070 | 11.425359375 | 3.286311556 |
| 3 | multirow_two_phase_scratch | 10 | 10.522659570 | 7.841837891 | 13.322815430 | 3.507553190 |
| 5 | current_execute_loop | 10 | 17.863931543 | 15.929815430 | 19.570296875 | 3.572786309 |
| 5 | multirow_interleaved_scratch | 10 | 14.714591016 | 13.569592773 | 16.364211914 | 2.942918203 |
| 5 | multirow_two_phase_scratch | 10 | 16.025151660 | 14.846522461 | 17.743687500 | 3.205030332 |

## Comparison

| rows | variant | baseline_mean_per_group_us | variant_mean_per_group_us | speedup_vs_current | promotion_threshold | decision |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | multirow_interleaved_scratch | 12.136842481 | 9.858934668 | 1.231050097 | 1.030000 | PROMOTE_COMPONENT_PROBE |
| 3 | multirow_two_phase_scratch | 12.136842481 | 10.522659570 | 1.153400659 | 1.030000 | PROMOTE_COMPONENT_PROBE |
| 5 | multirow_interleaved_scratch | 17.863931543 | 14.714591016 | 1.214028411 | 1.030000 | PROMOTE_COMPONENT_PROBE |
| 5 | multirow_two_phase_scratch | 17.863931543 | 16.025151660 | 1.114743369 | 1.030000 | PROMOTE_COMPONENT_PROBE |

## Gates

| gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- |
| G1_stage211_entry | PASS | stage211_proof_present | 1 | repro/stage211_fft_dataflow_preflight/proof_gate.csv | Stage212 is entered only after Stage211 denies direct hot-path code and admits backend/API probing. |
| G2_build_compile | PASS | build_rc;compile_rc | 0;0 | repro/stage212_multirow_fft_api_probe/build_static.log; repro/stage212_multirow_fft_api_probe/compile_probe.log | Build current spqlios_avx512 static library and compile standalone multirow reverse-DFT probe. |
| G3_correctness | PASS | all_variant_mismatches | 0 | repro/stage212_multirow_fft_api_probe/correctness.csv | Multirow wrapper variants must match current execute_reverse_torus64 output exactly. |
| G4_microbench_promotion | PASS_PROMOTE | min_best_speedup_across_3row_5row;best_speedup_any | 1.214028411;1.231050097 | repro/stage212_multirow_fft_api_probe/comparison.csv | Promotion requires >= 1.03x for both 3-row and 5-row groups. |
| G5_stage212_decision | PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213 | decision | PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213 | repro/stage212_multirow_fft_api_probe/proof_gate.csv | Stage212 either promotes a standalone wrapper probe to a later integration gate or closes this local wrapper route. |

## Next Queue

| priority | route | entry_condition | gate | status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage213_flag_only_sab_dft_wrapper_integration_preflight | Stage212 promotes multirow wrapper component probe. | Flag-only SAB preflight with staged equivalence and full SAB A/B. | ready | repro/stage212_multirow_fft_api_probe/proof_gate.csv |
| P1 | native_counter_or_true_backend_fft_design | Stage212 local wrapper is not promoted or needs hardware attribution. | Use native perf counters or implement a genuinely new backend batch FFT primitive outside SAB first. | ready | repro/stage212_multirow_fft_api_probe/comparison.csv |
| P2 | sab_hotpath_integration | A component probe is promoted and then passes staged SAB gates. | Correctness, noise/resource, complete-SAB T_bootstrap/r A/B, and claim audit. | requires_stage213 | repro/stage212_multirow_fft_api_probe/proof_gate.csv |
