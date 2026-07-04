# Artifact Manifest

Code artifacts:

- `include/sab_pvw.h`
- `src/sab_pvw.c`
- `main.c` gated test path under `SAB_PVW_KERNEL_TEST`
- `src/mosfhet/Makefile.def` gated PVW flags:
  - `SAB_PVW_KERNEL_TEST`
  - `SAB_PVW_TARGET_TEST`
  - `SAB_PVW_BENCH`
  - `SAB_PVW_BENCH_R`
  - `SAB_PVW_BENCH_REPS`
  - `SAB_PVW_RESOURCE_TEST`
  - `SAB_PVW_RESOURCE_R`
  - `SAB_PVW_NOISE_TEST`
  - `SAB_PVW_NOISE_R`
  - `SAB_PVW_NOISE_TRIALS`
  - `SAB_PVW_NOISE_MAX_LOG2_GAP`
  - `SAB_PVW_STAGE_NOISE_TEST`
  - `MOSFHET_DETERMINISTIC_RNG`
  - `MOSFHET_TEST_RNG_SEED`
  - `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED`
  - `SAB_PVW_POSTPROC_PROFILE`
  - `SAB_PVW_BODY_PROFILE`
  - `SAB_PVW_FUSED_FROM_DFT_ADD`
  - `SAB_PVW_ACTIVE_BUFFER_FUSION`
  - `SAB_PVW_SUBA_OUTPUT_FUSION`
  - `SAB_PVW_SCHEDULE_FUSED_CMUX`
- `src/mosfhet/include/mosfhet.h` PVW sample-array declaration
- `src/mosfhet/src/misc.c` deterministic test RNG path
- `src/mosfhet/src/mattrgsw.c` experimental small-r AVX512 MAT external-product dispatch
- `scripts/run_stage6_seed_sweep.sh`
- `scripts/run_stage6_seed_sweep_range.sh`
- `scripts/run_stage7_bench_sweep.sh`
- `scripts/run_stage11_avx512_smallr_bench.sh`
- `scripts/run_stage13_postproc_profile.sh`
- `scripts/run_stage14_body_profile.sh`
- `scripts/run_stage15_avx512_mat_gate.sh`
- `scripts/run_stage16_full_sab_audit.sh`
- `scripts/run_stage17_perf_attribution.sh`
- `scripts/run_stage18_cmux_profile.sh`
- `scripts/run_stage19_sparse_schedule_audit.sh`
- `scripts/run_stage20_active_buffer_profile.sh`
- `scripts/run_stage20_active_buffer_bench.sh`
- `scripts/run_stage21_suba_output_profile.sh`
- `scripts/run_stage21_suba_output_bench.sh`
- `scripts/run_stage22_mat_avx512_limit_audit.sh`
- `scripts/run_stage23_schedule_fused_profile.sh`
- `scripts/run_stage23_schedule_fused_bench.sh`
- `scripts/run_stage24_postproc_tail_profile.sh`
- `scripts/run_stage25_final_noise_sweep.sh`
- `scripts/run_stage25_stage_noise_probe.sh`
- `scripts/run_stage25_resource_matrix.sh`
- `scripts/run_stage26_parameter_target_smoke.sh`
- `scripts/run_stage26_parameter_perf_noise.sh`
- `scripts/run_stage27_related_work_access_probe.py`
- `scripts/run_stage27_citation_access_probe.sh`
- `scripts/build_stage27_final_package.py`
- `scripts/run_stage28_native_perf_counter_gate.sh`
- `scripts/build_final_goal_completion_audit.py`
- `scripts/build_remaining_blocker_dashboard.py`
- `scripts/run_final_goal_recheck.sh`
- `scripts/register_external_evidence.py`
- `scripts/run_stage33_current_smoke.sh`
- `scripts/build_stage35_completion_blockers.py`
- `scripts/build_conditional_backlog_audit.py`
- `scripts/build_stage36_high_stat_plan.py`
- `scripts/run_stage36_high_stat_expansion.sh`
- `scripts/build_stage36_target_perf_summary.py`
- `scripts/run_stage36_stage_noise_sweep.sh`
- `scripts/build_stage36_resource_summary.py`
- `scripts/run_stage37_native_perf_counter_audit.sh`
- `scripts/build_stage37_native_perf_counter_log.py`
- `scripts/run_stage38_fulltext_review_gate.sh`
- `scripts/build_stage38_fulltext_review_gate.py`
- `scripts/build_stage38_fulltext_review_log.py`
- `scripts/build_stage39_variant_triage.py`
- `scripts/build_stage40_final_freeze.py`
- `scripts/verify_stage40_freeze.py`
- `scripts/build_stage41_external_unlock_packet.py`
- `scripts/build_stage42_evidence_closure_audit.py`
- `scripts/verify_stage42_closure.py`
- `scripts/run_stage44_external_unlock_reprobe.sh`
- `scripts/build_stage44_external_unlock_reprobe.py`

Documentation artifacts:

- `docs/roadmap_686_pvw_sab.md`
- `docs/mat_to_bootstrap_goal_audit.md`
- `docs/stage5_pvw_sparse_mul_log.md`
- `docs/stage5_pvw_bootstrap_wo_extract_log.md`
- `docs/stage5_pvw_extract_log.md`
- `docs/stage5_pvw_packing_hwks_log.md`
- `docs/stage5_pvw_full_bootstrap_log.md`
- `docs/stage5_pvw_rgsw_monomial_log.md`
- `docs/stage6_pvw_noise_log.md`
- `docs/stage7_pvw_full_bench_log.md`
- `docs/stage8_ablation_plan.md`
- `docs/stage8_clear_elision_log.md`
- `docs/stage8_gain_separation.md`
- `docs/stage9_novelty_scan.md`
- `docs/stage9_statistical_evidence.md`
- `docs/stage9_stage_noise_probe.md`
- `docs/stage10_engineering_report.md`
- `docs/stage11_pvw_sab_loop_engineering.md`
- `docs/stage12_next_goal.md`
- `docs/stage12_avx512_gate_and_v2_kernel_log.md`
- `docs/stage13_postproc_profile_log.md`
- `docs/stage14_algorithm_to_paper_goal.md`
- `docs/stage14_body_profile_log.md`
- `docs/stage15_avx512_mat_expectation_log.md`
- `docs/stage16_full_sab_audit_log.md`
- `docs/stage16_plus_execution_plan.md`
- `docs/stage17_perf_attribution_log.md`
- `docs/stage18_cmux_profile_and_fusion_log.md`
- `docs/goal_sab_max_acceleration.md`
- `docs/roadmap_stage19_plus.md`
- `docs/loop_engineering.md`
- `docs/stage19_sparse_schedule_audit_log.md`
- `docs/stage20_active_buffer_log.md`
- `docs/stage21_suba_output_log.md`
- `docs/stage22_mat_avx512_limit_audit_log.md`
- `docs/stage23_schedule_fused_cmux_log.md`
- `docs/stage24_postproc_tail_log.md`
- `docs/stage25_correctness_noise_resource_log.md`
- `docs/stage26_parameter_branch_log.md`
- `docs/stage26_parameter_perf_noise_log.md`
- `docs/stage27_novelty_paper_package_log.md`
- `docs/stage27_full_related_work_gate_log.md`
- `docs/stage27_final_full_sab_performance_log.md`
- `docs/stage27_related_work_refresh_log.md`
- `docs/stage27_related_work_access_probe_log.md`
- `docs/stage27_citation_gate_log.md`
- `docs/stage27_final_evidence_package.md`
- `docs/stage27_completion_readiness_audit.md`
- `docs/stage27_final_engineering_report.md`
- `docs/stage28_native_perf_counter_gate_log.md`
- `docs/final_goal_completion_audit.md`
- `docs/remaining_blocker_dashboard.md`
- `docs/final_goal_recheck_log.md`
- `docs/external_evidence_intake_log.md`
- `docs/stage32_citation_refresh_log.md`
- `docs/stage33_current_smoke_log.md`
- `docs/stage34_current_smoke_recheck_log.md`
- `docs/stage35_completion_blocker_matrix.md`
- `docs/conditional_backlog_audit.md`
- `docs/stage36_high_stat_expansion_log.md`
- `docs/stage37_native_perf_counter_log.md`
- `docs/stage38_fulltext_review_log.md`
- `docs/stage39_variant_triage_log.md`
- `docs/stage40_final_freeze_report.md`
- `docs/stage40_postfreeze_verify_log.md`
- `docs/stage41_external_unlock_packet.md`
- `docs/stage42_evidence_closure_audit.md`
- `docs/stage42_closure_verify_log.md`
- `docs/stage43_postclosure_current_smoke_log.md`
- `docs/stage44_external_unlock_reprobe_log.md`
- `hypotheses/hypothesis_register.yaml`
- `algorithm_variants/pvw_sab_rspecialized_avx512.md`
- `algorithm_variants/pvw_sab_direct_lane_extract.md`
- `algorithm_variants/pvw_sab_full_pipeline.md`
- `theory_checks/pvw_sab_complexity_model.md`
- `theory_checks/mat_avx_memory_model.md`
- `experiments/stage11_experiment_validation_plan.md`
- `experiments/stage12_experiment_validation_plan.md`
- `experiments/stage13_postproc_validation_plan.md`
- `experiments/stage14_body_profile_validation_plan.md`
- `experiments/stage15_avx512_mat_validation_plan.md`
- `experiments/stage16_full_sab_audit_plan.md`
- `experiments/stage17_perf_attribution_plan.md`
- `experiments/stage18_cmux_profile_plan.md`
- `experiments/stage18_fused_from_dft_add_plan.md`
- `experiments/stage19_sparse_schedule_audit_plan.md`
- `experiments/stage20_active_buffer_validation_plan.md`
- `experiments/stage21_suba_output_validation_plan.md`
- `experiments/stage22_mat_avx512_limit_audit_plan.md`
- `experiments/stage23_schedule_fused_cmux_plan.md`
- `experiments/stage24_postproc_tail_plan.md`
- `experiments/stage25_correctness_noise_resource_plan.md`
- `experiments/stage26_parameter_branch_plan.md`
- `experiments/stage26_parameter_perf_noise_plan.md`
- `experiments/stage27_novelty_paper_package_plan.md`
- `experiments/stage28_native_perf_counter_gate_plan.md`
- `experiments/final_goal_recheck_plan.md`
- `experiments/external_evidence_intake_plan.md`
- `experiments/stage32_citation_refresh_plan.md`
- `experiments/stage33_current_smoke_plan.md`
- `experiments/stage34_current_smoke_recheck_plan.md`
- `experiments/stage35_completion_blockers_plan.md`
- `experiments/stage36_high_stat_expansion_plan.md`
- `experiments/stage37_native_perf_counter_plan.md`
- `experiments/stage38_fulltext_review_plan.md`
- `experiments/stage39_optional_variant_triage_plan.md`
- `experiments/stage40_final_freeze_plan.md`
- `experiments/stage40_postfreeze_verify_plan.md`
- `experiments/stage41_external_unlock_plan.md`
- `experiments/stage42_evidence_closure_audit_plan.md`
- `experiments/stage42_closure_verify_plan.md`
- `experiments/stage43_postclosure_current_smoke_plan.md`
- `experiments/stage44_external_unlock_reprobe_plan.md`

Repro artifacts:

- `repro/environment.md`
- `repro/baseline_registry.yaml`
- `repro/run_log.csv`
- `repro/stage_commit_registry.csv`
- `repro/reproduction_checklist.md`
- `repro/stage6_seed_sweep_smoke/summary.csv`
- `repro/stage6_seed_sweep_smoke/seed_6862025.log`
- `repro/stage6_seed_sweep_smoke/seed_6862026.log`
- `repro/stage6_seed_sweep_smoke/seed_6862027.log`
- `repro/stage6_seed_sweep_10/summary.csv`
- `repro/stage6_seed_sweep_10/seed_6862025.log`
- `repro/stage6_seed_sweep_10/seed_6862026.log`
- `repro/stage6_seed_sweep_10/seed_6862027.log`
- `repro/stage6_seed_sweep_10/seed_6862028.log`
- `repro/stage6_seed_sweep_10/seed_6862029.log`
- `repro/stage6_seed_sweep_10/seed_6862030.log`
- `repro/stage6_seed_sweep_10/seed_6862031.log`
- `repro/stage6_seed_sweep_10/seed_6862032.log`
- `repro/stage6_seed_sweep_10/seed_6862033.log`
- `repro/stage6_seed_sweep_10/seed_6862034.log`
- `repro/stage6_seed_sweep_50/summary.csv`
- `repro/stage6_seed_sweep_50/seed_6862025.log` through
  `repro/stage6_seed_sweep_50/seed_6862074.log`
- `repro/stage6_seed_sweep_r4_smoke/summary.csv`
- `repro/stage6_seed_sweep_r4_smoke/seed_6862025.log`
- `repro/stage6_seed_sweep_r4_10/summary.csv`
- `repro/stage6_seed_sweep_r4_10/seed_6862025.log` through
  `repro/stage6_seed_sweep_r4_10/seed_6862034.log`
- `repro/stage7_pvw_bench_r4_reps3/main.log`
- `repro/stage7_full_bench_summary.csv`
- `repro/stage7_resource_r2/pvw.log`
- `repro/stage7_resource_r2/pvw.time.log`
- `repro/stage7_resource_r2/scalar.log`
- `repro/stage7_resource_r2/scalar.time.log`
- `repro/stage7_resource_r4/pvw.log`
- `repro/stage7_resource_r4/pvw.time.log`
- `repro/stage7_resource_r4/scalar.log`
- `repro/stage7_resource_r4/scalar.time.log`
- `repro/stage7_resource_summary.csv`
- `repro/stage7_bench_sweep_r2_reps2_runs3/summary.csv`
- `repro/stage7_bench_sweep_r2_reps2_runs3/run_0.log`
- `repro/stage7_bench_sweep_r2_reps2_runs3/run_1.log`
- `repro/stage7_bench_sweep_r2_reps2_runs3/run_2.log`
- `repro/stage7_bench_sweep_r4_reps2_runs3/summary.csv`
- `repro/stage7_bench_sweep_r4_reps2_runs3/run_0.log`
- `repro/stage7_bench_sweep_r4_reps2_runs3/run_1.log`
- `repro/stage7_bench_sweep_r4_reps2_runs3/run_2.log`
- `repro/stage7_bench_sweep_summary.csv`
- `repro/stage7_backend_ffnt_r2_reps1_runs1/summary.csv`
- `repro/stage7_backend_ffnt_r2_reps1_runs1/run_0.log`
- `repro/stage7_backend_summary.csv`
- `repro/stage8_r_scaling_r1_reps2_runs3/summary.csv`
- `repro/stage8_r_scaling_r1_reps2_runs3/run_0.log`
- `repro/stage8_r_scaling_r1_reps2_runs3/run_1.log`
- `repro/stage8_r_scaling_r1_reps2_runs3/run_2.log`
- `repro/stage8_r_scaling_summary.csv`
- `repro/stage8_backend_avx512_r2_reps1_runs1/summary.csv`
- `repro/stage8_backend_avx512_r2_reps1_runs1/run_0.log`
- `repro/stage8_backend_sensitivity_summary.csv`
- `repro/stage8_backend_avx512_r2_reps2_runs3/summary.csv`
- `repro/stage8_backend_avx512_r2_reps2_runs3/run_0.log`
- `repro/stage8_backend_avx512_r2_reps2_runs3/run_1.log`
- `repro/stage8_backend_avx512_r2_reps2_runs3/run_2.log`
- `repro/stage8_backend_avx512_r4_reps2_runs3/summary.csv`
- `repro/stage8_backend_avx512_r4_reps2_runs3/run_0.log`
- `repro/stage8_backend_avx512_r4_reps2_runs3/run_1.log`
- `repro/stage8_backend_avx512_r4_reps2_runs3/run_2.log`
- `repro/stage8_clear_elision_kernel_spqlios/main.log`
- `repro/stage8_clear_elision_target_spqlios/main.log`
- `repro/stage8_clear_elision_scalar_spqlios/main.log`
- `repro/stage8_clear_elision_summary.csv`
- `repro/stage8_clear_elision_bench_r4_reps2_runs3/summary.csv`
- `repro/stage8_clear_elision_bench_r4_reps2_runs3/run_0.log`
- `repro/stage8_clear_elision_bench_r4_reps2_runs3/run_1.log`
- `repro/stage8_clear_elision_bench_r4_reps2_runs3/run_2.log`
- `repro/stage8_clear_elision_bench_summary.csv`
- `repro/stage8_clear_elision_bench_r2_reps2_runs3/summary.csv`
- `repro/stage8_clear_elision_bench_r2_reps2_runs3/run_0.log`
- `repro/stage8_clear_elision_bench_r2_reps2_runs3/run_1.log`
- `repro/stage8_clear_elision_bench_r2_reps2_runs3/run_2.log`
- `repro/stage8_clear_elision_noise_r2_trials3/main.log`
- `repro/stage8_clear_elision_noise_r4_trials1/main.log`
- `repro/stage8_clear_elision_noise_summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_50_aggregate.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_10/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_10/seed_6862025.log` through
  `repro/stage8_clear_elision_seed_sweep_r2_10/seed_6862034.log`
- `repro/stage8_clear_elision_seed_sweep_r2_40_more/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_40_more/seed_6862035.log`
  through `repro/stage8_clear_elision_seed_sweep_r2_40_more/seed_6862074.log`
- `repro/stage8_clear_elision_seed_sweep_r4_10/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r4_10/seed_6862025.log` through
  `repro/stage8_clear_elision_seed_sweep_r4_10/seed_6862034.log`
- `repro/stage8_clear_elision_seed_sweep_r4_50_aggregate.csv`
- `repro/stage8_clear_elision_seed_sweep_r4_40_more/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r4_40_more/seed_6862035.log`
  through `repro/stage8_clear_elision_seed_sweep_r4_40_more/seed_6862074.log`
- `repro/stage8_clear_elision_seed_sweep_summary.csv`
- `repro/stage8_full_bootstrap_gain_separation.csv`
- `repro/stage9_literature_matrix.csv`
- `repro/stage9_failure_rate_summary.csv`
- `repro/stage9_stage_noise_r2_trials1/main.log`
- `repro/stage9_stage_noise_r4_trials1/main.log`
- `repro/stage9_stage_noise_summary.csv`
- `repro/stage10_claim_evidence_matrix.csv`
- `repro/stage11_avx512_rspecialized_summary.csv`
- `repro/stage11_avx512_rspecialized_kernel/main.log`
- `repro/stage11_avx512_smallr_explicit_kernel_fail/main.log`
- `repro/stage11_avx512_smallr_replay_target_r2/main.log`
- `repro/stage11_avx512_rspecialized_r2_reps2_runs3/summary.csv`
- `repro/stage11_avx512_rspecialized_r2_reps2_runs3/run_0.log`
- `repro/stage11_avx512_rspecialized_r2_reps2_runs3/run_1.log`
- `repro/stage11_avx512_rspecialized_r2_reps2_runs3/run_2.log`
- `repro/stage11_avx512_rspecialized_r4_reps2_runs3/summary.csv`
- `repro/stage11_avx512_rspecialized_r4_reps2_runs3/run_0.log`
- `repro/stage11_avx512_rspecialized_r4_reps2_runs3/run_1.log`
- `repro/stage11_avx512_smallr_replay_r2_reps1_runs1/summary.csv`
- `repro/stage11_avx512_smallr_replay_r2_reps1_runs1/run_0.log`
- `repro/stage11_avx512_smallr_replay_r4_reps1_runs1/summary.csv`
- `repro/stage11_avx512_smallr_replay_r4_reps1_runs1/run_0.log`
- `repro/stage12_avx512_v2_summary.csv`
- `repro/stage12_avx512_default_kernel_check/main.log`
- `repro/stage12_avx512_default_kernel_progress/main.log`
- `repro/stage12_avx512_default_sparse_progress/main.log`
- `repro/stage12_avx512_default_kernel_fixed/main.log`
- `repro/stage12_avx512_smallr_kernel_fixed/main.log`
- `repro/stage12_spqlios_kernel_regression/main.log`
- `repro/stage12_avx512_default_target_full/main.log`
- `repro/stage12_avx512_smallr_v2_kernel/main.log`
- `repro/stage12_avx512_smallr_v2_target_full/main.log`
- `repro/stage12_avx512_smallr_v2_bench_r2_reps1_runs1/summary.csv`
- `repro/stage12_avx512_smallr_v2_bench_r2_reps1_runs1/run_0.log`
- `repro/stage12_avx512_smallr_v2_bench_r4_reps1_runs1/summary.csv`
- `repro/stage12_avx512_smallr_v2_bench_r4_reps1_runs1/run_0.log`
- `repro/stage13_postproc_summary.csv`
- `repro/stage13_kernel_spqlios_direct_extract.log`
- `repro/stage13_kernel_spqlios_direct_extract_fixed.log`
- `repro/stage13_target_full_spqlios_direct_extract.log`
- `repro/stage13_postproc_profile_r2_reps1_runs1/postproc_profile.csv`
- `repro/stage13_postproc_profile_r2_reps1_runs1/bench_summary.csv`
- `repro/stage13_postproc_profile_r2_reps1_runs1/run_0.log`
- `repro/stage13_postproc_profile_r4_reps1_runs1/postproc_profile.csv`
- `repro/stage13_postproc_profile_r4_reps1_runs1/bench_summary.csv`
- `repro/stage13_postproc_profile_r4_reps1_runs1/run_0.log`
- `repro/stage13_direct_extract_bench_r2_reps1_runs1/summary.csv`
- `repro/stage13_direct_extract_bench_r2_reps1_runs1/run_0.log`
- `repro/stage13_direct_extract_bench_r4_reps1_runs1/summary.csv`
- `repro/stage13_direct_extract_bench_r4_reps1_runs1/run_0.log`
- `repro/stage14_body_profile_summary.csv`
- `repro/stage14_spqlios_kernel_regression.log`
- `repro/stage14_body_profile_r2_reps1_runs1/body_profile.csv`
- `repro/stage14_body_profile_r2_reps1_runs1/bench_summary.csv`
- `repro/stage14_body_profile_r2_reps1_runs1/run_0.log`
- `repro/stage14_body_profile_r4_reps1_runs1/body_profile.csv`
- `repro/stage14_body_profile_r4_reps1_runs1/bench_summary.csv`
- `repro/stage14_body_profile_r4_reps1_runs1/run_0.log`
- `repro/stage15_avx512_mat_summary.csv`
- `repro/stage15_avx512_mat_baseline_kernel.log`
- `repro/stage15_avx512_mat_v3_kernel.log`
- `repro/stage15_avx512_mat_v3_kernel_runs3/run_0.log`
- `repro/stage15_avx512_mat_v3_kernel_runs3/run_1.log`
- `repro/stage15_avx512_mat_v3_kernel_runs3/run_2.log`
- `repro/stage15_avx512_mat_instruction_snippet.txt`
- `repro/stage15_avx512_mat_gate_runs3/mat_vs_scalar.csv`
- `repro/stage15_avx512_mat_gate_runs3/mat_full_vs_scalar.csv`
- `repro/stage15_avx512_mat_gate_runs3/ep_breakdown.csv`
- `repro/stage15_avx512_mat_gate_runs3/run_0.log`
- `repro/stage15_avx512_mat_gate_runs3/run_1.log`
- `repro/stage15_avx512_mat_gate_runs3/run_2.log`
- `repro/stage15_avx512_mat_target_full.log`
- `repro/stage15_avx512_mat_full_sab_r2_reps1_runs1/summary.csv`
- `repro/stage15_avx512_mat_full_sab_r2_reps1_runs1/run_0.log`
- `repro/stage15_avx512_mat_full_sab_r4_reps1_runs1/summary.csv`
- `repro/stage15_avx512_mat_full_sab_r4_reps1_runs1/run_0.log`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/summary.csv`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r2/summary.csv`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r2/run_0.log`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r2/run_1.log`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r2/run_2.log`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r4/summary.csv`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r4/run_0.log`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r4/run_1.log`
- `repro/stage16_avx512_full_sab_audit_runs3_reps1/r4/run_2.log`
- `repro/stage17_perf_attribution_r2/summary.csv`
- `repro/stage17_perf_attribution_r2/r2/run.log`
- `repro/stage17_perf_attribution_r2/r2/time.log`
- `repro/stage17_perf_attribution_r2/r2/perf.log`
- `repro/stage17_perf_attribution_r2/r2/mattrgsw_instruction_snippet.txt`
- `repro/stage17_perf_attribution_r4/summary.csv`
- `repro/stage17_perf_attribution_r4/r4/run.log`
- `repro/stage17_perf_attribution_r4/r4/time.log`
- `repro/stage17_perf_attribution_r4/r4/perf.log`
- `repro/stage17_perf_attribution_r4/r4/mattrgsw_instruction_snippet.txt`
- `repro/stage18_cmux_profile_avx512_r2_runs1/summary.csv`
- `repro/stage18_cmux_profile_avx512_r2_runs1/r2/run_0.log`
- `repro/stage18_cmux_profile_avx512_r4_runs1/summary.csv`
- `repro/stage18_cmux_profile_avx512_r4_runs1/r4/run_0.log`
- `repro/stage18_fused_from_dft_add_kernel.log`
- `repro/stage18_fused_from_dft_add_target_full.log`
- `repro/stage18_default_avx512_target_full_regression.log`
- `repro/stage18_fused_from_dft_add_r2_reps1_runs1/summary.csv`
- `repro/stage18_fused_from_dft_add_r2_reps1_runs1/run_0.log`
- `repro/stage18_fused_from_dft_add_r4_reps1_runs1/summary.csv`
- `repro/stage18_fused_from_dft_add_r4_reps1_runs1/run_0.log`
- `repro/stage18_fused_from_dft_add_r4_runs3_reps1/summary.csv`
- `repro/stage18_fused_from_dft_add_r4_runs3_reps1/r4/summary.csv`
- `repro/stage18_fused_from_dft_add_r4_runs3_reps1/r4/run_0.log`
- `repro/stage18_fused_from_dft_add_r4_runs3_reps1/r4/run_1.log`
- `repro/stage18_fused_from_dft_add_r4_runs3_reps1/r4/run_2.log`
- `repro/stage19_sparse_schedule_avx512_runs1/summary.csv`
- `repro/stage19_sparse_schedule_avx512_runs1/bit_counts.csv`
- `repro/stage19_sparse_schedule_avx512_runs1/r2/run_0.log`
- `repro/stage19_sparse_schedule_avx512_runs1/r4/run_0.log`
- `repro/stage20_active_buffer_summary.csv`
- `repro/stage20_active_buffer_target_full.log`
- `repro/stage20_default_target_regression.log`
- `repro/stage20_active_buffer_profile_avx512_runs1/summary.csv`
- `repro/stage20_active_buffer_profile_avx512_runs1/r2/run_0.log`
- `repro/stage20_active_buffer_profile_avx512_runs1/r4/run_0.log`
- `repro/stage20_active_buffer_bench_r2_reps1_runs3/summary.csv`
- `repro/stage20_active_buffer_bench_r2_reps1_runs3/run_0.log`
- `repro/stage20_active_buffer_bench_r2_reps1_runs3/run_1.log`
- `repro/stage20_active_buffer_bench_r2_reps1_runs3/run_2.log`
- `repro/stage20_active_buffer_bench_r4_reps1_runs3/summary.csv`
- `repro/stage20_active_buffer_bench_r4_reps1_runs3/run_0.log`
- `repro/stage20_active_buffer_bench_r4_reps1_runs3/run_1.log`
- `repro/stage20_active_buffer_bench_r4_reps1_runs3/run_2.log`
- `repro/stage21_suba_output_summary.csv`
- `repro/stage21_suba_output_target_full.log`
- `repro/stage21_default_target_regression.log`
- `repro/stage21_suba_output_profile_avx512_runs1/summary.csv`
- `repro/stage21_suba_output_profile_avx512_runs1/r2/run_0.log`
- `repro/stage21_suba_output_profile_avx512_runs1/r4/run_0.log`
- `repro/stage21_suba_output_bench_r2_reps1_runs1_seq/summary.csv`
- `repro/stage21_suba_output_bench_r2_reps1_runs1_seq/run_0.log`
- `repro/stage21_suba_output_bench_r4_reps1_runs1_seq/summary.csv`
- `repro/stage21_suba_output_bench_r4_reps1_runs1_seq/run_0.log`
- `repro/stage22_mat_avx512_summary.csv`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/kernel_microbench.csv`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/full_sab_smoke.csv`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/ep_breakdown.csv`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/instruction_counts.csv`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/generic/kernel_run_0.log`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/generic/objdump_mattrgsw_polynomial.txt`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/generic/full_r2/run_0.log`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/generic/full_r4/run_0.log`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/specialized/kernel_run_0.log`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/specialized/objdump_mattrgsw_polynomial.txt`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/specialized/full_r2/run_0.log`
- `repro/stage22_mat_avx512_limit_audit_runs1_full1/specialized/full_r4/run_0.log`
- `repro/stage22_mat_avx512_full_r4_runs3/kernel_microbench.csv`
- `repro/stage22_mat_avx512_full_r4_runs3/full_sab_smoke.csv`
- `repro/stage22_mat_avx512_full_r4_runs3/ep_breakdown.csv`
- `repro/stage22_mat_avx512_full_r4_runs3/instruction_counts.csv`
- `repro/stage22_mat_avx512_full_r4_runs3/generic/kernel_run_0.log`
- `repro/stage22_mat_avx512_full_r4_runs3/generic/objdump_mattrgsw_polynomial.txt`
- `repro/stage22_mat_avx512_full_r4_runs3/generic/full_r4/run_0.log`
- `repro/stage22_mat_avx512_full_r4_runs3/generic/full_r4/run_1.log`
- `repro/stage22_mat_avx512_full_r4_runs3/generic/full_r4/run_2.log`
- `repro/stage22_mat_avx512_full_r4_runs3/specialized/kernel_run_0.log`
- `repro/stage22_mat_avx512_full_r4_runs3/specialized/objdump_mattrgsw_polynomial.txt`
- `repro/stage22_mat_avx512_full_r4_runs3/specialized/full_r4/run_0.log`
- `repro/stage22_mat_avx512_full_r4_runs3/specialized/full_r4/run_1.log`
- `repro/stage22_mat_avx512_full_r4_runs3/specialized/full_r4/run_2.log`
- `experiments/stage23_schedule_fused_cmux_plan.md`
- `docs/stage23_schedule_fused_cmux_log.md`
- `scripts/run_stage23_schedule_fused_profile.sh`
- `scripts/run_stage23_schedule_fused_bench.sh`
- `repro/stage23_schedule_fused_summary.csv`
- `repro/stage23_schedule_fused_target_full.log`
- `repro/stage23_default_target_regression.log`
- `repro/stage23_schedule_fused_profile_avx512_runs1/summary.csv`
- `repro/stage23_schedule_fused_profile_avx512_runs1/r2/run_0.log`
- `repro/stage23_schedule_fused_profile_avx512_runs1/r4/run_0.log`
- `repro/stage23_schedule_fused_bench_r2_reps1_runs3_seq/summary.csv`
- `repro/stage23_schedule_fused_bench_r2_reps1_runs3_seq/run_0.log`
- `repro/stage23_schedule_fused_bench_r2_reps1_runs3_seq/run_1.log`
- `repro/stage23_schedule_fused_bench_r2_reps1_runs3_seq/run_2.log`
- `repro/stage23_schedule_fused_bench_r4_reps1_runs3_seq/summary.csv`
- `repro/stage23_schedule_fused_bench_r4_reps1_runs3_seq/run_0.log`
- `repro/stage23_schedule_fused_bench_r4_reps1_runs3_seq/run_1.log`
- `repro/stage23_schedule_fused_bench_r4_reps1_runs3_seq/run_2.log`
- `repro/stage23_schedule_fused_bench_r2_reps1_runs3/summary.csv`
- `repro/stage23_schedule_fused_bench_r4_reps1_runs3/summary.csv`
- `experiments/stage24_postproc_tail_plan.md`
- `docs/stage24_postproc_tail_log.md`
- `scripts/run_stage24_postproc_tail_profile.sh`
- `repro/stage24_postproc_tail_avx512_runs1/postproc_samples.csv`
- `repro/stage24_postproc_tail_avx512_runs1/summary.csv`
- `repro/stage24_postproc_tail_avx512_runs1/r2/run_0.log`
- `repro/stage24_postproc_tail_avx512_runs1/r4/run_0.log`
- `repro/stage25_final_noise_avx512_seeds1/summary.csv`
- `repro/stage25_final_noise_avx512_seeds1/aggregate.csv`
- `repro/stage25_final_noise_avx512_seeds1/r1/seed_6862025.log`
- `repro/stage25_final_noise_avx512_seeds1/r2/seed_6862025.log`
- `repro/stage25_final_noise_avx512_seeds1/r4/seed_6862025.log`
- `repro/stage25_final_noise_avx512_r2_r4_seeds50/summary.csv`
- `repro/stage25_final_noise_avx512_r2_r4_seeds50/aggregate.csv`
- `repro/stage25_final_noise_avx512_r2_r4_seeds50/r2/seed_6862025.log`
  through `repro/stage25_final_noise_avx512_r2_r4_seeds50/r2/seed_6862074.log`
- `repro/stage25_final_noise_avx512_r2_r4_seeds50/r4/seed_6862025.log`
  through `repro/stage25_final_noise_avx512_r2_r4_seeds50/r4/seed_6862074.log`
- `repro/stage25_stage_noise_avx512_trials1/summary.csv`
- `repro/stage25_stage_noise_avx512_trials1/r1/seed_6862025.log`
- `repro/stage25_stage_noise_avx512_trials1/r2/seed_6862025.log`
- `repro/stage25_stage_noise_avx512_trials1/r4/seed_6862025.log`
- `repro/stage25_resource_avx512/summary.csv`
- `repro/stage25_resource_avx512/r1/pvw.log`
- `repro/stage25_resource_avx512/r1/pvw.time.log`
- `repro/stage25_resource_avx512/r1/scalar.log`
- `repro/stage25_resource_avx512/r1/scalar.time.log`
- `repro/stage25_resource_avx512/r2/pvw.log`
- `repro/stage25_resource_avx512/r2/pvw.time.log`
- `repro/stage25_resource_avx512/r2/scalar.log`
- `repro/stage25_resource_avx512/r2/scalar.time.log`
- `repro/stage25_resource_avx512/r4/pvw.log`
- `repro/stage25_resource_avx512/r4/pvw.time.log`
- `repro/stage25_resource_avx512/r4/scalar.log`
- `repro/stage25_resource_avx512/r4/scalar.time.log`
- `repro/stage26_parameter_branch_smoke_avx512/parameter_summary.csv`
- `repro/stage26_parameter_branch_smoke_avx512/branch_summary.csv`
- `repro/stage26_parameter_branch_smoke_avx512/binary_SET_2_3_2048/build.log`
- `repro/stage26_parameter_branch_smoke_avx512/binary_SET_2_3_2048/run.log`
- `repro/stage26_parameter_branch_smoke_avx512/binary_SET_4_5_2048/build.log`
- `repro/stage26_parameter_branch_smoke_avx512/binary_SET_4_5_2048/run.log`
- `repro/stage26_parameter_branch_smoke_avx512/binary_SET_2_3_4096/build.log`
- `repro/stage26_parameter_branch_smoke_avx512/binary_SET_2_3_4096/run.log`
- `repro/stage26_parameter_branch_smoke_avx512/unsupported_TERNARY_SET_2_3_2048/pvw_build.log`
- `repro/stage26_parameter_branch_smoke_avx512/unsupported_TERNARY_SET_2_3_2048/scalar_build.log`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/perf_SET_4_5_2048_r2_runs1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/perf_SET_2_3_4096_r2_runs1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/noise_SET_4_5_2048_r2_seeds1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/noise_SET_4_5_2048_r2_seeds1/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/noise_SET_2_3_4096_r2_seeds1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_smoke/noise_SET_2_3_4096_r2_seeds1/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_smoke/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_smoke/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_smoke/perf_SET_4_5_2048_r4_runs1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_smoke/noise_SET_4_5_2048_r4_seeds1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_smoke/noise_SET_4_5_2048_r4_seeds1/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_runs3_seeds3/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_runs3_seeds3/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_runs3_seeds3/perf_SET_4_5_2048_r4_runs3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_runs3_seeds3/noise_SET_4_5_2048_r4_seeds3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_4_5_2048_r4_runs3_seeds3/noise_SET_4_5_2048_r4_seeds3/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_smoke/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_smoke/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_smoke/perf_SET_2_3_4096_r4_runs1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_smoke/noise_SET_2_3_4096_r4_seeds1/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_smoke/noise_SET_2_3_4096_r4_seeds1/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_runs3_seeds3/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_runs3_seeds3/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_runs3_seeds3/perf_SET_2_3_4096_r4_runs3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_runs3_seeds3/noise_SET_2_3_4096_r4_seeds3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_set_2_3_4096_r4_runs3_seeds3/noise_SET_2_3_4096_r4_seeds3/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/perf_SET_4_5_2048_r2_runs3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/perf_SET_2_3_4096_r2_runs3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/noise_SET_4_5_2048_r2_seeds3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/noise_SET_4_5_2048_r2_seeds3/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/noise_SET_2_3_4096_r2_seeds3/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_r2_runs3_seeds3/noise_SET_2_3_4096_r2_seeds3/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/performance_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/performance_stats.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/perf_SET_4_5_2048_r2_runs5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/perf_SET_4_5_2048_r4_runs5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/perf_SET_2_3_4096_r2_runs5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/perf_SET_2_3_4096_r4_runs5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_4_5_2048_r2_seeds5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_4_5_2048_r2_seeds5/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_4_5_2048_r4_seeds5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_4_5_2048_r4_seeds5/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_2_3_4096_r2_seeds5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_2_3_4096_r2_seeds5/aggregate.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_2_3_4096_r4_seeds5/summary.csv`
- `repro/stage26_parameter_perf_noise_avx512_added_binary_r2_r4_runs5_seeds5/noise_SET_2_3_4096_r4_seeds5/aggregate.csv`
- `repro/stage27_literature_matrix.csv`
- `repro/stage27_source_access_matrix.csv`
- `repro/stage27_related_work_access_refresh.csv`
- `repro/stage27_related_work_access_probe/access_probe.csv`
- `repro/stage27_related_work_access_probe/summary.csv`
- `repro/stage27_claim_support_matrix.csv`
- `repro/stage27_citation_access_probe/access_probe.csv`
- `repro/stage27_citation_access_probe/summary.csv`
- `repro/stage27_completion_readiness_audit.csv`
- `repro/stage27_final_full_sab_summary.csv`
- `repro/stage27_final_evidence_package/performance_scope.csv`
- `repro/stage27_final_evidence_package/noise_scope.csv`
- `repro/stage27_final_evidence_package/resource_scope.csv`
- `repro/stage27_final_evidence_package/claim_scope.csv`
- `repro/stage27_final_evidence_package/citation_gate.csv`
- `repro/stage27_final_evidence_package/completion_readiness.csv`
- `repro/stage27_final_evidence_package/manifest.csv`
- `repro/stage27_final_full_sab_active_r2_runs3/summary.csv`
- `repro/stage27_final_full_sab_active_r2_runs3/run_0.log`
- `repro/stage27_final_full_sab_active_r2_runs3/run_1.log`
- `repro/stage27_final_full_sab_active_r2_runs3/run_2.log`
- `repro/stage27_final_full_sab_active_r4_runs3/summary.csv`
- `repro/stage27_final_full_sab_active_r4_runs3/run_0.log`
- `repro/stage27_final_full_sab_active_r4_runs3/run_1.log`
- `repro/stage27_final_full_sab_active_r4_runs3/run_2.log`
- `repro/stage28_native_perf_counter_gate/summary.csv`
- `repro/stage28_native_perf_counter_gate/environment.log`
- `repro/stage28_native_perf_counter_gate/perf_smoke.log`
- `repro/final_goal_completion_audit.csv`
- `repro/remaining_blocker_dashboard.csv`
- `repro/final_goal_recheck/summary.csv`
- `repro/final_goal_recheck/stage28_perf_gate.log`
- `repro/final_goal_recheck/stage27_citation_probe.log`
- `repro/final_goal_recheck/stage27_related_work_access_probe.log`
- `repro/final_goal_recheck/stage27_final_package.log`
- `repro/final_goal_recheck/external_evidence_intake.log`
- `repro/final_goal_recheck/stage33_current_smoke.log`
- `repro/final_goal_recheck/conditional_backlog_audit.log`
- `repro/final_goal_recheck/final_goal_audit.log`
- `repro/final_goal_recheck/remaining_blocker_dashboard.log`
- `repro/final_goal_recheck/stage40_postfreeze_verify.log`
- `repro/final_goal_recheck/stage70_external_unlock_preflight.log`
- `repro/final_goal_recheck/stage42_evidence_closure.log`
- `repro/final_goal_recheck_postfreeze/summary.csv`
- `repro/final_goal_recheck_postfreeze/stage40_postfreeze_verify.log`
- `repro/final_goal_recheck_stage42_closure/summary.csv`
- `repro/final_goal_recheck_stage42_closure/stage42_evidence_closure.log`
- `repro/final_goal_recheck_stage44_reprobe/summary.csv`
- `repro/final_goal_recheck_stage44_reprobe/stage44_external_reprobe.log`
- `repro/final_goal_recheck_stage44_reprobe/final_goal_audit.log`
- `repro/final_goal_recheck_stage44_reprobe/stage42_evidence_closure.log`
- `repro/external_evidence_intake/summary.csv`
- `repro/stage35_completion_blockers.csv`
- `repro/conditional_backlog_audit.csv`
- `repro/stage36_high_stat_plan.csv`
- `repro/stage36_target_perf_summary.csv`
- `repro/stage36_target_perf_samples.csv`
- `repro/stage36_target_perf_exclusions.csv`
- `repro/stage36_target_perf_supplemental.csv`
- `repro/stage36_target_perf_r2_runs10/summary.csv`
- `repro/stage36_target_perf_r2_runs10/run_0.log` through
  `repro/stage36_target_perf_r2_runs10/run_9.log`
- `repro/stage36_target_perf_r4_runs10/summary.csv`
- `repro/stage36_target_perf_r4_runs10/run_0.log` through
  `repro/stage36_target_perf_r4_runs10/run_9.log`
- `repro/stage36_target_perf_r4_runs2_topup/summary.csv`
- `repro/stage36_target_perf_r4_runs2_topup/run_0.log`
- `repro/stage36_target_perf_r4_runs2_topup/run_1.log`
- `docs/stage36_target_noise_expansion_log.md`
- `repro/stage36_target_noise_seeds50/summary.csv`
- `repro/stage36_target_noise_seeds50/aggregate.csv`
- `repro/stage36_target_noise_seeds50/r2/seed_6862025.log` through
  `repro/stage36_target_noise_seeds50/r2/seed_6862074.log`
- `repro/stage36_target_noise_seeds50/r4/seed_6862025.log` through
  `repro/stage36_target_noise_seeds50/r4/seed_6862074.log`
- `repro/stage36_stage_noise_seeds10/summary.csv`
- `repro/stage36_stage_noise_seeds10/aggregate.csv`
- `repro/stage36_stage_noise_seeds10/r2/seed_6864025.log` through
  `repro/stage36_stage_noise_seeds10/r2/seed_6864034.log`
- `repro/stage36_stage_noise_seeds10/r4/seed_6864025.log` through
  `repro/stage36_stage_noise_seeds10/r4/seed_6864034.log`
- `repro/stage36_resource_summary.csv`
- `repro/stage36_resource_samples.csv`
- `repro/stage36_resource_run_0/summary.csv`
- `repro/stage36_resource_run_1/summary.csv`
- `repro/stage36_resource_run_2/summary.csv`
- `repro/stage36_resource_run_0/r1/pvw.log` through
  `repro/stage36_resource_run_2/r4/scalar.time.log`
- `scripts/build_stage36_added_params_summary.py`
- `docs/stage36_added_params_expansion_log.md`
- `repro/stage36_added_params_runs10_seeds20/performance_summary.csv`
- `repro/stage36_added_params_runs10_seeds20/performance_stats.csv`
- `repro/stage36_added_params_runs10_seeds20/performance_samples.csv`
- `repro/stage36_added_params_runs10_seeds20/performance_supplemental.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_summary.csv`
- `repro/stage36_added_params_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/perf_SET_2_3_4096_r4_runs9_topup/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/aggregate.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/aggregate.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/aggregate.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/summary.csv`
- `repro/stage36_added_params_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/aggregate.csv`
- `repro/stage37_native_perf_counter_audit/summary.csv`
- `repro/stage37_native_perf_counter_audit/stage28_gate/summary.csv`
- `repro/stage37_native_perf_counter_audit/stage28_gate/environment.log`
- `repro/stage37_native_perf_counter_audit/stage28_gate/perf_smoke.log`
- `repro/stage37_native_perf_counter_audit/stage28_gate.log`
- `repro/stage37_native_perf_counter_audit/external_evidence_intake.log`
- `repro/stage37_native_perf_counter_audit/final_goal_audit.log`
- `repro/stage37_native_perf_counter_audit/stage35_blockers.log`
- `repro/stage37_native_perf_counter_audit/stage37_log_builder.log`
- `repro/stage38_fulltext_review_gate/summary.csv`
- `repro/stage38_fulltext_review_gate/review_checklist.csv`
- `repro/stage38_fulltext_review_gate/fulltext_gate.log`
- `repro/stage38_fulltext_review_gate/external_evidence_intake.log`
- `repro/stage38_fulltext_review_gate/final_goal_audit.log`
- `repro/stage38_fulltext_review_gate/stage35_blockers.log`
- `repro/stage38_fulltext_review_gate/stage38_log_builder.log`
- `repro/stage39_variant_triage.csv`
- `repro/stage40_final_freeze_summary.csv`
- `repro/stage40_final_freeze_manifest.csv`
- `repro/stage40_postfreeze_verify/summary.csv`
- `repro/stage41_external_unlock_packet.csv`
- `repro/stage42_evidence_closure_audit.csv`
- `repro/stage42_evidence_closure_manifest.csv`
- `repro/stage42_closure_verify/summary.csv`
- `repro/stage43_current_smoke_after_stage42/summary.csv`
- `repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/build.log`
- `repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/run.log`
- `repro/stage43_current_smoke_after_stage42/scalar_ternary_SET_2_3_2048/build.log`
- `repro/stage44_external_unlock_reprobe/summary.csv`
- `repro/stage44_external_unlock_reprobe/citation_probe.log`
- `repro/stage44_external_unlock_reprobe/citation_probe/summary.csv`
- `repro/stage44_external_unlock_reprobe/citation_probe/access_probe.csv`
- `repro/stage44_external_unlock_reprobe/native_perf_gate.log`
- `repro/stage44_external_unlock_reprobe/native_perf_gate/summary.csv`
- `repro/stage44_external_unlock_reprobe/native_perf_gate/environment.log`
- `repro/stage44_external_unlock_reprobe/native_perf_gate/perf_smoke.log`
- `repro/stage44_external_unlock_reprobe/external_evidence_intake.log`
- `repro/stage44_external_unlock_reprobe/stage44_log_builder.log`
- `repro/stage33_current_smoke/summary.csv`
- `repro/stage33_current_smoke/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage33_current_smoke/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage33_current_smoke/pvw_target_SET_2_3_2048/build.log`
- `repro/stage33_current_smoke/pvw_target_SET_2_3_2048/run.log`
- `repro/stage33_current_smoke/scalar_ternary_SET_2_3_2048/build.log`
- `docs/stage45_active_state_refactor_log.md`
- `repro/stage45_active_state_refactor/summary.csv`
- `repro/stage45_active_state_refactor/ffnt_kernel_build.log`
- `repro/stage45_active_state_refactor/ffnt_kernel_run.log`
- `repro/stage45_active_state_refactor/spqlios_avx512_windows_build.log`
- `docs/stage46_wsl_active_state_target_smoke_log.md`
- `repro/stage46_wsl_active_state_target_smoke/summary.csv`
- `repro/stage46_wsl_active_state_target_smoke/build.log`
- `repro/stage46_wsl_active_state_target_smoke/run.log`
- `docs/stage47_wsl_full_sab_smoke_log.md`
- `repro/stage47_wsl_active_state_full_sab_smoke/summary.csv`
- `repro/stage47_wsl_active_state_full_sab_smoke/r2/summary.csv`
- `repro/stage47_wsl_active_state_full_sab_smoke/r2/run_0.log`
- `repro/stage47_wsl_active_state_full_sab_smoke/r4/summary.csv`
- `repro/stage47_wsl_active_state_full_sab_smoke/r4/run_0.log`
- `docs/stage48_wsl_noise_smoke_log.md`
- `repro/stage48_wsl_active_state_noise_smoke/summary.csv`
- `repro/stage48_wsl_active_state_noise_smoke/aggregate.csv`
- `repro/stage48_wsl_active_state_noise_smoke/r2/seed_6862025.log`
- `repro/stage48_wsl_active_state_noise_smoke/r4/seed_6862025.log`
- `docs/stage49_wsl_repeated_full_sab_log.md`
- `repro/stage49_wsl_repeated_full_sab/summary.csv`
- `repro/stage49_wsl_repeated_full_sab/r2/summary.csv`
- `repro/stage49_wsl_repeated_full_sab/r2/driver.log`
- `repro/stage49_wsl_repeated_full_sab/r2/run_0.log`
- `repro/stage49_wsl_repeated_full_sab/r2/run_1.log`
- `repro/stage49_wsl_repeated_full_sab/r2/run_2.log`
- `repro/stage49_wsl_repeated_full_sab/r4/summary.csv`
- `repro/stage49_wsl_repeated_full_sab/r4/driver.log`
- `repro/stage49_wsl_repeated_full_sab/r4/run_0.log`
- `repro/stage49_wsl_repeated_full_sab/r4/run_1.log`
- `repro/stage49_wsl_repeated_full_sab/r4/run_2.log`
- `docs/stage50_performance_evidence_matrix.md`
- `scripts/build_stage50_performance_evidence_matrix.py`
- `repro/stage50_performance_evidence_matrix.csv`
- `docs/stage51_goal_completion_frontier.md`
- `scripts/build_stage51_goal_completion_frontier.py`
- `repro/stage51_goal_completion_frontier.csv`
- `docs/stage52_external_unlock_readiness.md`
- `scripts/build_stage52_external_unlock_readiness.py`
- `repro/stage52_external_unlock_readiness.csv`
- `docs/stage53_final_recheck_integration_log.md`
- `scripts/run_final_goal_recheck.sh`
- `repro/stage53_final_recheck_stage50_52/summary.csv`
- `repro/stage53_final_recheck_stage50_52/final_goal_audit.log`
- `repro/stage53_final_recheck_stage50_52/remaining_blocker_dashboard.log`
- `repro/stage53_final_recheck_stage50_52/stage50_performance_matrix.log`
- `repro/stage53_final_recheck_stage50_52/stage51_goal_frontier.log`
- `repro/stage53_final_recheck_stage50_52/stage52_external_unlock_readiness.log`
- `repro/stage53_final_recheck_stage50_52/stage42_evidence_closure.log`
- `docs/stage54_default_final_recheck_log.md`
- `repro/stage54_default_final_recheck/summary.csv`
- `repro/stage54_default_final_recheck/stage28_perf_gate.log`
- `repro/stage54_default_final_recheck/stage27_final_package.log`
- `repro/stage54_default_final_recheck/external_evidence_intake.log`
- `repro/stage54_default_final_recheck/conditional_backlog_audit.log`
- `repro/stage54_default_final_recheck/final_goal_audit.log`
- `repro/stage54_default_final_recheck/remaining_blocker_dashboard.log`
- `repro/stage54_default_final_recheck/stage50_performance_matrix.log`
- `repro/stage54_default_final_recheck/stage51_goal_frontier.log`
- `repro/stage54_default_final_recheck/stage52_external_unlock_readiness.log`
- `repro/stage54_default_final_recheck/stage42_evidence_closure.log`

## Stage 55 External Paper Probe

- `docs/stage55_external_paper_probe_log.md`
- `scripts/build_stage55_external_paper_probe.py`
- `repro/stage55_external_paper_probe/summary.csv`
- `repro/stage55_external_paper_probe/access_probe.csv`
- `repro/stage55_external_paper_probe/crossref_summary.csv`
- `repro/stage55_external_paper_probe/crossref_metadata.json`

## Stage 56 Stage55 Final-Recheck Integration

- `docs/stage56_final_recheck_stage55_log.md`
- `scripts/run_final_goal_recheck.sh`
- `repro/stage56_final_recheck_stage55/summary.csv`
- `repro/stage56_final_recheck_stage55/stage55_external_paper_probe.log`
- `repro/stage56_final_recheck_stage55/final_goal_audit.log`
- `repro/stage56_final_recheck_stage55/remaining_blocker_dashboard.log`
- `repro/stage56_final_recheck_stage55/stage51_goal_frontier.log`
- `repro/stage56_final_recheck_stage55/stage52_external_unlock_readiness.log`
- `repro/stage56_final_recheck_stage55/stage42_evidence_closure.log`

## Stage 57 Scope Label Consistency Audit

- `docs/stage57_scope_label_audit.md`
- `scripts/build_stage57_scope_label_audit.py`
- `scripts/build_stage51_goal_completion_frontier.py`
- `docs/stage51_goal_completion_frontier.md`
- `repro/stage51_goal_completion_frontier.csv`
- `docs/stage52_external_unlock_readiness.md`
- `repro/stage52_external_unlock_readiness.csv`
- `repro/stage57_scope_label_audit.csv`

## Stage 58 Stage57 Final-Recheck Integration

- `docs/stage58_final_recheck_stage57_log.md`
- `scripts/run_final_goal_recheck.sh`
- `repro/stage58_final_recheck_stage57/summary.csv`
- `repro/stage58_final_recheck_stage57/final_goal_audit.log`
- `repro/stage58_final_recheck_stage57/remaining_blocker_dashboard.log`
- `repro/stage58_final_recheck_stage57/stage51_goal_frontier.log`
- `repro/stage58_final_recheck_stage57/stage52_external_unlock_readiness.log`
- `repro/stage58_final_recheck_stage57/stage57_scope_label_audit.log`
- `repro/stage58_final_recheck_stage57/stage42_evidence_closure.log`

## Stage 59 Completion Route Readiness

- `docs/roadmap_to_completion_after_stage58.md`
- `docs/stage59_completion_route_readiness.md`
- `scripts/build_stage59_completion_route_readiness.py`
- `repro/stage59_completion_route_readiness.csv`

## Stage 60 Stage59 Final-Recheck Integration

- `docs/stage60_final_recheck_stage59_log.md`
- `scripts/run_final_goal_recheck.sh`
- `repro/stage60_final_recheck_stage59/summary.csv`
- `repro/stage60_final_recheck_stage59/final_goal_audit.log`
- `repro/stage60_final_recheck_stage59/remaining_blocker_dashboard.log`
- `repro/stage60_final_recheck_stage59/stage51_goal_frontier.log`
- `repro/stage60_final_recheck_stage59/stage52_external_unlock_readiness.log`
- `repro/stage60_final_recheck_stage59/stage57_scope_label_audit.log`
- `repro/stage60_final_recheck_stage59/stage59_completion_route.log`
- `repro/stage60_final_recheck_stage59/stage42_evidence_closure.log`
- `repro/stage60_final_recheck_stage59_failed_attempt1/summary.csv`
- `repro/stage60_final_recheck_stage59_failed_attempt1/stage42_evidence_closure.log`
- `repro/stage60_final_recheck_stage59_failed_attempt2/summary.csv`
- `repro/stage60_final_recheck_stage59_failed_attempt2/stage51_goal_frontier.log`
- `repro/stage60_final_recheck_stage59_failed_attempt3/summary.csv`
- `repro/stage60_final_recheck_stage59_failed_attempt3/stage42_evidence_closure.log`
- `repro/stage60_final_recheck_stage59_failed_attempt4/summary.csv`
- `repro/stage60_final_recheck_stage59_failed_attempt4/stage42_evidence_closure.log`

## Stage 61 Native Perf Unlock Probe

- `docs/stage61_native_perf_unlock_probe_log.md`
- `scripts/run_stage28_native_perf_counter_gate.sh`
- `repro/stage61_native_perf_unlock_probe/summary.csv`
- `repro/stage61_native_perf_unlock_probe/environment.log`
- `repro/stage61_native_perf_unlock_probe/perf_smoke.log`

## Stage 62 Full-Text Unlock Probe

- `docs/stage62_fulltext_unlock_probe_log.md`
- `scripts/build_stage62_fulltext_unlock_probe.py`
- `repro/stage62_fulltext_unlock_probe/unlock_summary.csv`
- `repro/stage62_fulltext_unlock_probe/summary.csv`
- `repro/stage62_fulltext_unlock_probe/review_checklist.csv`
- `repro/stage62_fulltext_unlock_probe/fulltext_gate.log`
- `repro/stage62_fulltext_unlock_probe/acm_pdf_head.log`
- `repro/stage62_fulltext_unlock_probe/acm_pdf_head.err`
- `repro/stage62_fulltext_unlock_probe/eprint_pdf_head.log`
- `repro/stage62_fulltext_unlock_probe/eprint_pdf_head.err`
- `repro/external_evidence_intake/summary.csv`

## Stage 64A Post-Variant Refresh

- `docs/stage64_post_variant_refresh_log.md`
- `scripts/run_stage64_post_variant_refresh.sh`
- `scripts/build_stage64_post_variant_refresh_log.py`
- `repro/stage64_post_variant_refresh/summary.csv`
- `repro/stage64_post_variant_refresh/run.log`
- `repro/stage64_post_variant_refresh/current_smoke/summary.csv`
- `repro/stage64_post_variant_refresh/current_smoke/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage64_post_variant_refresh/current_smoke/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage64_post_variant_refresh/current_smoke/pvw_target_SET_2_3_2048/build.log`
- `repro/stage64_post_variant_refresh/current_smoke/pvw_target_SET_2_3_2048/run.log`
- `repro/stage64_post_variant_refresh/current_smoke/scalar_ternary_SET_2_3_2048/build.log`
- `repro/stage64_post_variant_refresh/full_sab_r2/summary.csv`
- `repro/stage64_post_variant_refresh/full_sab_r2/run_0.log`
- `repro/stage64_post_variant_refresh/full_sab_r2/run_1.log`
- `repro/stage64_post_variant_refresh/full_sab_r2/run_2.log`
- `repro/stage64_post_variant_refresh/full_sab_r4/summary.csv`
- `repro/stage64_post_variant_refresh/full_sab_r4/run_0.log`
- `repro/stage64_post_variant_refresh/full_sab_r4/run_1.log`
- `repro/stage64_post_variant_refresh/full_sab_r4/run_2.log`
- `repro/stage64_post_variant_refresh/final_noise/summary.csv`
- `repro/stage64_post_variant_refresh/final_noise/aggregate.csv`
- `repro/stage64_post_variant_refresh/final_noise/r2/seed_6864025.log`
- `repro/stage64_post_variant_refresh/final_noise/r4/seed_6864025.log`

## Stage 65A R4 Unrolled AVX512 Variant

- `docs/stage65_r4_unrolled_avx512_log.md`
- `experiments/stage65_r4_unrolled_avx512_plan.md`
- `algorithm_variants/pvw_sab_r4_unrolled_avx512.md`
- `scripts/run_stage65_r4_unrolled_avx512.sh`
- `scripts/build_stage65_r4_unrolled_avx512_log.py`
- `repro/stage65_r4_unrolled_avx512/summary.csv`
- `repro/stage65_r4_unrolled_avx512/kernel_microbench.csv`
- `repro/stage65_r4_unrolled_avx512/full_sab_smoke.csv`
- `repro/stage65_r4_unrolled_avx512/instruction_counts.csv`
- `repro/stage65_r4_unrolled_avx512/run.log`
- `repro/stage65_r4_unrolled_avx512/default_scalar_ffnt_smoke.log`
- `repro/stage65_r4_unrolled_avx512/specialized/kernel_run_0.log`
- `repro/stage65_r4_unrolled_avx512/specialized/full_r4/run_0.log`
- `repro/stage65_r4_unrolled_avx512/specialized/objdump_mattrgsw_polynomial.txt`
- `repro/stage65_r4_unrolled_avx512/r4_unrolled/kernel_run_0.log`
- `repro/stage65_r4_unrolled_avx512/r4_unrolled/full_r4/run_0.log`
- `repro/stage65_r4_unrolled_avx512/r4_unrolled/objdump_mattrgsw_polynomial.txt`

## Stage 66A Post-Variant Final Recheck

- `docs/stage66_post_variant_final_recheck_log.md`
- `experiments/stage66_post_variant_final_recheck_plan.md`
- `scripts/run_stage66_post_variant_final_recheck.sh`
- `scripts/build_stage66_post_variant_final_recheck_log.py`
- `repro/stage66_post_variant_final_recheck/summary.csv`
- `repro/stage66_post_variant_final_recheck/final_recheck/summary.csv`
- `repro/stage66_post_variant_final_recheck/final_recheck/stage27_final_package.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/external_evidence_intake.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/conditional_backlog_audit.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/final_goal_audit.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/remaining_blocker_dashboard.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/stage50_performance_matrix.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/stage51_goal_frontier.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/stage52_external_unlock_readiness.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/stage57_scope_label_audit.log`
- `repro/stage66_post_variant_final_recheck/final_recheck/stage59_completion_route.log`

## Stage 67 Final-Recheck Stage66A Integration

- `docs/stage67_final_recheck_stage66_log.md`
- `experiments/stage67_final_recheck_stage66_plan.md`
- `scripts/build_stage67_final_recheck_stage66_log.py`
- `scripts/run_final_goal_recheck.sh`
- `repro/stage67_final_recheck_stage66/summary.csv`
- `repro/stage67_final_recheck_stage66/decision.csv`
- `repro/stage67_final_recheck_stage66/stage66_post_variant_final_recheck.log`

## Stage 68 Frontier Closure Consistency

- `docs/stage68_frontier_closure_consistency_log.md`
- `experiments/stage68_frontier_closure_consistency_plan.md`
- `scripts/build_stage68_frontier_closure_consistency.py`
- `repro/stage68_frontier_closure_consistency.csv`

## Stage 69 Local Variant Feasibility

- `docs/stage69_local_variant_feasibility_log.md`
- `experiments/stage69_local_variant_feasibility_plan.md`
- `scripts/build_stage69_local_variant_feasibility.py`
- `repro/stage69_local_variant_feasibility.csv`
- `theory_checks/h3_sparse_selector_feasibility.md`
- `algorithm_variants/pvw_sab_sparse_selector_shortcut.md`

## Stage 70 External Unlock Preflight

- `docs/stage70_external_unlock_preflight_log.md`
- `experiments/stage70_external_unlock_preflight_plan.md`
- `scripts/build_stage70_external_unlock_preflight.py`
- `repro/stage70_external_unlock_preflight.csv`

## Stage 71 Final-Recheck Stage70 Integration

- `docs/stage71_final_recheck_stage70_log.md`
- `experiments/stage71_final_recheck_stage70_plan.md`
- `scripts/build_stage71_final_recheck_stage70_log.py`
- `repro/stage71_final_recheck_stage70/summary.csv`
- `repro/stage71_final_recheck_stage70/decision.csv`
- `repro/stage71_final_recheck_stage70/final_goal_audit.log`
- `repro/stage71_final_recheck_stage70/remaining_blocker_dashboard.log`
- `repro/stage71_final_recheck_stage70/stage51_goal_frontier.log`
- `repro/stage71_final_recheck_stage70/stage52_external_unlock_readiness.log`
- `repro/stage71_final_recheck_stage70/stage57_scope_label_audit.log`
- `repro/stage71_final_recheck_stage70/stage59_completion_route.log`
- `repro/stage71_final_recheck_stage70/stage70_external_unlock_preflight.log`
- `repro/stage71_final_recheck_stage70/stage42_evidence_closure.log`
- `repro/stage71_final_recheck_stage70_failed_attempt1/decision.csv`
- `repro/stage71_final_recheck_stage70_failed_attempt1/stage71_log_failed.md`

## Stage 72 External Source Refresh

- `docs/stage72_external_source_refresh_log.md`
- `experiments/stage72_external_source_refresh_plan.md`
- `scripts/build_stage72_external_source_refresh.py`
- `repro/stage72_external_source_refresh/summary.csv`
- `repro/stage72_external_source_refresh/access_probe.csv`
- `repro/stage72_external_source_refresh/crossref_summary.csv`
- `repro/stage72_external_source_refresh/crossref_metadata.json`
- `repro/stage72_external_source_refresh/author_cite.bib`

## Stage 73 Final-Recheck Stage72 Integration

- `docs/stage73_final_recheck_stage72_log.md`
- `experiments/stage73_final_recheck_stage72_plan.md`
- `scripts/build_stage73_final_recheck_stage72_log.py`
- `scripts/run_final_goal_recheck.sh`
- `repro/stage73_final_recheck_stage72/summary.csv`
- `repro/stage73_final_recheck_stage72/decision.csv`
- `repro/stage73_final_recheck_stage72/stage72_external_source_refresh.log`
- `repro/stage73_final_recheck_stage72/final_goal_audit.log`
- `repro/stage73_final_recheck_stage72/remaining_blocker_dashboard.log`
- `repro/stage73_final_recheck_stage72/stage51_goal_frontier.log`
- `repro/stage73_final_recheck_stage72/stage52_external_unlock_readiness.log`
- `repro/stage73_final_recheck_stage72/stage57_scope_label_audit.log`
- `repro/stage73_final_recheck_stage72/stage59_completion_route.log`
- `repro/stage73_final_recheck_stage72/stage70_external_unlock_preflight.log`
- `repro/stage73_final_recheck_stage72/stage42_evidence_closure.log`

## Stage 74 R-Scaling Boundary

- `docs/stage74_r_scaling_boundary_log.md`
- `experiments/stage74_r_scaling_boundary_plan.md`
- `scripts/build_stage74_r_scaling_boundary.py`
- `theory_checks/h10_r_gt4_lane_scaling.md`
- `algorithm_variants/pvw_sab_r_gt4_lane_scaling.md`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage74_r_scaling_boundary/decision.csv`
- `repro/stage74_r_scaling_boundary/r6_reps1_runs1/summary.csv`
- `repro/stage74_r_scaling_boundary/r6_reps1_runs1/run_0.log`
- `repro/stage74_r_scaling_boundary/r8_reps1_runs1/summary.csv`
- `repro/stage74_r_scaling_boundary/r8_reps1_runs1/run_0.log`

## Stage 75 R>4 Profile Boundary

- `docs/stage75_rgt4_profile_boundary_log.md`
- `experiments/stage75_rgt4_profile_boundary_plan.md`
- `scripts/build_stage75_rgt4_profile_boundary.py`
- `theory_checks/h10_r_gt4_lane_scaling.md`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage75_rgt4_profile_boundary/decision.csv`
- `repro/stage75_rgt4_profile_boundary/profile_metrics.csv`
- `repro/stage75_rgt4_profile_boundary/body_profile_r6/summary.csv`
- `repro/stage75_rgt4_profile_boundary/body_profile_r6/r6/run_0.log`
- `repro/stage75_rgt4_profile_boundary/body_profile_r8/summary.csv`
- `repro/stage75_rgt4_profile_boundary/body_profile_r8/r8/run_0.log`

## Stage 76 R>4 Kernel Feasibility

- `docs/stage76_rgt4_kernel_feasibility_log.md`
- `experiments/stage76_rgt4_kernel_feasibility_plan.md`
- `scripts/build_stage76_rgt4_kernel_feasibility.py`
- `theory_checks/h11_rgt4_fused_mat_kernel.md`
- `algorithm_variants/pvw_sab_rgt4_fused_mat_kernel.md`
- `hypotheses/hypothesis_register.yaml`
- `main.c`
- `src/mosfhet/Makefile.def`
- `repro/stage76_rgt4_kernel_feasibility/rgt4_kernel_smoke.log`
- `repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv`
- `repro/stage76_rgt4_kernel_feasibility/ep_breakdown.csv`
- `repro/stage76_rgt4_kernel_feasibility/summary.csv`

## Stage 77 R>4 Fused MAT Kernel

- `docs/stage77_rgt4_fused_mat_kernel_log.md`
- `experiments/stage77_rgt4_fused_mat_kernel_plan.md`
- `scripts/build_stage77_rgt4_fused_mat_kernel.py`
- `theory_checks/h11_rgt4_fused_mat_kernel.md`
- `algorithm_variants/pvw_sab_rgt4_fused_mat_kernel.md`
- `hypotheses/hypothesis_register.yaml`
- `src/mosfhet/Makefile.def`
- `src/mosfhet/src/mattrgsw.c`
- `repro/stage77_rgt4_fused_mat_kernel/generic.log`
- `repro/stage77_rgt4_fused_mat_kernel/fused.log`
- `repro/stage77_rgt4_fused_mat_kernel/kernel_comparison.csv`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_smoke.csv`
- `repro/stage77_rgt4_fused_mat_kernel/summary.csv`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r6/summary.csv`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r6/run_0.log`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r8/summary.csv`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r8/run_0.log`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r6/summary.csv`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r6/run_0.log`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r8/summary.csv`
- `repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r8/run_0.log`

## Stage 78 R>4 Fused Repeated Gates

- `docs/stage78_rgt4_fused_repeated_gates_log.md`
- `experiments/stage78_rgt4_fused_repeated_gates_plan.md`
- `scripts/run_stage78_rgt4_fused_repeated_gates.sh`
- `scripts/build_stage78_rgt4_fused_repeated_gates.py`
- `repro/stage78_rgt4_fused_repeated_gates/stage78_run.log`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_repeated.csv`
- `repro/stage78_rgt4_fused_repeated_gates/summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/run_0.log`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/run_1.log`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/run_2.log`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r8_runs1/summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r8_runs1/run_0.log`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/aggregate.csv`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/r6/seed_6862025.log`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/r6/seed_6862026.log`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/r6/seed_6862027.log`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/r8/seed_6862025.log`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/r8/seed_6862026.log`
- `repro/stage78_rgt4_fused_repeated_gates/final_noise/r8/seed_6862027.log`
- `repro/stage78_rgt4_fused_repeated_gates/noise_summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/resource/summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/resource_summary.csv`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r6/pvw.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r6/pvw.time.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r6/scalar.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r6/scalar.time.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r8/pvw.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r8/pvw.time.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r8/scalar.log`
- `repro/stage78_rgt4_fused_repeated_gates/resource/r8/scalar.time.log`

## Stage 79 R>4 Fused High-Stat Confirmation

- `docs/stage79_rgt4_fused_high_stat_log.md`
- `experiments/stage79_rgt4_fused_high_stat_plan.md`
- `scripts/run_stage79_rgt4_fused_high_stat.sh`
- `scripts/build_stage79_rgt4_fused_high_stat.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage79_rgt4_fused_high_stat/stage79_run.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_high_stat.csv`
- `repro/stage79_rgt4_fused_high_stat/noise_summary.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_samples.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_summary.csv`
- `repro/stage79_rgt4_fused_high_stat/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_0.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_1.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_2.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_3.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_4.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_5.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_6.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_7.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_8.log`
- `repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_9.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/final_noise/aggregate.csv`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866025.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866026.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866027.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866028.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866029.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866030.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866031.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866032.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866033.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866034.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866035.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866036.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866037.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866038.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866039.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866040.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866041.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866042.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866043.log`
- `repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866044.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_0/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/pvw.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/pvw.time.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/scalar.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/scalar.time.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_1/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/pvw.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/pvw.time.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/scalar.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/scalar.time.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_2/summary.csv`
- `repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/pvw.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/pvw.time.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/scalar.log`
- `repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/scalar.time.log`

## Stage 80 Promotion Policy Audit

- `docs/stage80_promotion_policy_audit_log.md`
- `experiments/stage80_promotion_policy_audit_plan.md`
- `scripts/run_stage80_promotion_policy_audit.sh`
- `scripts/build_stage80_promotion_policy_audit.py`
- `repro/stage80_promotion_policy_audit/stage80_run.log`
- `repro/stage80_promotion_policy_audit/summary.csv`
- `repro/stage80_promotion_policy_audit/current_smoke/summary.csv`
- `repro/stage80_promotion_policy_audit/current_smoke/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage80_promotion_policy_audit/current_smoke/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage80_promotion_policy_audit/current_smoke/pvw_target_SET_2_3_2048/build.log`
- `repro/stage80_promotion_policy_audit/current_smoke/pvw_target_SET_2_3_2048/run.log`
- `repro/stage80_promotion_policy_audit/current_smoke/scalar_ternary_SET_2_3_2048/build.log`

## Stage 81 Next Variant Triage

- `docs/stage81_next_variant_triage_log.md`
- `experiments/stage81_next_variant_triage_plan.md`
- `scripts/build_stage81_next_variant_triage.py`
- `repro/stage81_next_variant_triage.csv`

## Stage 82 Post-H11 Fused R6 Profile

- `docs/stage82_post_h11_profile_log.md`
- `experiments/stage82_post_h11_profile_plan.md`
- `scripts/run_stage82_post_h11_profile.sh`
- `scripts/build_stage82_post_h11_profile.py`
- `repro/stage82_post_h11_profile/stage82_run.log`
- `repro/stage82_post_h11_profile/body_profile_fused_r6/summary.csv`
- `repro/stage82_post_h11_profile/body_profile_fused_r6/r6/run_0.log`
- `repro/stage82_post_h11_profile/profile_metrics.csv`
- `repro/stage82_post_h11_profile/decision.csv`

## Stage 83 MAT Body Design Check

- `docs/stage83_mat_body_design_check_log.md`
- `experiments/stage83_mat_body_design_check_plan.md`
- `scripts/build_stage83_mat_body_design_check.py`
- `theory_checks/h13_mat_body_reduction_design.md`
- `algorithm_variants/pvw_sab_h13_mat_body_design.md`
- `repro/stage83_mat_body_design_check/candidates.csv`
- `repro/stage83_mat_body_design_check/decision.csv`

## Stage 84 H13 R6 Tile-Sweep Preflight

- `docs/stage84_h13_r6_tile_sweep_preflight_log.md`
- `experiments/stage84_h13_r6_tile_sweep_preflight_plan.md`
- `scripts/run_stage84_h13_r6_tile_sweep_preflight.sh`
- `scripts/build_stage84_h13_r6_tile_sweep_preflight.py`
- `src/mosfhet/Makefile.def`
- `src/mosfhet/src/mattrgsw.c`
- `repro/stage84_h13_r6_tile_sweep_preflight/stage84_run.log`
- `repro/stage84_h13_r6_tile_sweep_preflight/tile4.log`
- `repro/stage84_h13_r6_tile_sweep_preflight/fulltile.log`
- `repro/stage84_h13_r6_tile_sweep_preflight/kernel_comparison.csv`
- `repro/stage84_h13_r6_tile_sweep_preflight/full_sab_smoke.csv`
- `repro/stage84_h13_r6_tile_sweep_preflight/summary.csv`
- `repro/stage84_h13_r6_tile_sweep_preflight/full_sab_tile4_r6/summary.csv`
- `repro/stage84_h13_r6_tile_sweep_preflight/full_sab_tile4_r6/run_0.log`
- `repro/stage84_h13_r6_tile_sweep_preflight/full_sab_fulltile_r6/summary.csv`
- `repro/stage84_h13_r6_tile_sweep_preflight/full_sab_fulltile_r6/run_0.log`

## Stage 86 Secondary CMUX Materialization

- `docs/stage86_secondary_cmux_materialization_log.md`
- `experiments/stage86_secondary_cmux_materialization_plan.md`
- `scripts/build_stage86_secondary_cmux_materialization.py`
- `theory_checks/h14_secondary_cmux_materialization.md`
- `algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md`
- `repro/stage86_secondary_cmux_materialization/candidates.csv`
- `repro/stage86_secondary_cmux_materialization/decision.csv`

## Stage 87 H14 Backend FromDFT-Add Preflight

- `docs/stage87_h14_backend_from_dft_add_preflight_log.md`
- `experiments/stage87_h14_backend_from_dft_add_preflight_plan.md`
- `scripts/run_stage87_h14_backend_from_dft_add_preflight.sh`
- `scripts/build_stage87_h14_backend_from_dft_add_preflight.py`
- `theory_checks/h14_secondary_cmux_materialization.md`
- `algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md`
- `src/mosfhet/Makefile.def`
- `src/mosfhet/include/mosfhet.h`
- `src/mosfhet/src/polynomial.c`
- `src/mosfhet/src/pvwtmlwe.c`
- `src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c`
- `src/mosfhet/src/fft/spqlios/spqlios-fft.h`
- `src/mosfhet/src/fft/ffnt/ffnt.c`
- `src/mosfhet/src/fft/ffnt/ffnt.h`
- `repro/stage87_h14_backend_from_dft_add_preflight/kernel_build.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/kernel_run.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/target_build.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/target_run.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/full_sab_wrapper_r6/build.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/full_sab_wrapper_r6/run_0.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/full_sab_backend_r6/build.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/full_sab_backend_r6/run_0.log`
- `repro/stage87_h14_backend_from_dft_add_preflight/full_sab_smoke.csv`
- `repro/stage87_h14_backend_from_dft_add_preflight/summary.csv`

## Stage 88 H14 Backend Repeated Gates

- `docs/stage88_h14_backend_repeated_gates_log.md`
- `experiments/stage88_h14_backend_repeated_gates_plan.md`
- `scripts/run_stage88_h14_backend_repeated_gates.sh`
- `scripts/build_stage88_h14_backend_repeated_gates.py`
- `theory_checks/h14_secondary_cmux_materialization.md`
- `algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md`
- `repro/stage88_h14_backend_repeated_gates/stage88_run.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/build.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/run_0.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/run_1.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/run_2.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/summary.csv`
- `repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/build.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/run_0.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/run_1.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/run_2.log`
- `repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/summary.csv`
- `repro/stage88_h14_backend_repeated_gates/full_sab_repeated.csv`
- `repro/stage88_h14_backend_repeated_gates/backend_vs_wrapper.csv`
- `repro/stage88_h14_backend_repeated_gates/final_noise/summary.csv`
- `repro/stage88_h14_backend_repeated_gates/final_noise/aggregate.csv`
- `repro/stage88_h14_backend_repeated_gates/final_noise/r6/seed_6868025.log`
- `repro/stage88_h14_backend_repeated_gates/final_noise/r6/seed_6868026.log`
- `repro/stage88_h14_backend_repeated_gates/final_noise/r6/seed_6868027.log`
- `repro/stage88_h14_backend_repeated_gates/noise_summary.csv`
- `repro/stage88_h14_backend_repeated_gates/resource_run_0/summary.csv`
- `repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/pvw.log`
- `repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/pvw.time.log`
- `repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/scalar.log`
- `repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/scalar.time.log`
- `repro/stage88_h14_backend_repeated_gates/resource_samples.csv`
- `repro/stage88_h14_backend_repeated_gates/resource_summary.csv`
- `repro/stage88_h14_backend_repeated_gates/summary.csv`

## Stage 89 H14 Promotion Policy Integration

- `docs/stage89_h14_promotion_policy_integration_log.md`
- `experiments/stage89_h14_promotion_policy_integration_plan.md`
- `scripts/run_stage89_h14_promotion_policy_integration.sh`
- `scripts/build_stage89_h14_promotion_policy_integration.py`
- `theory_checks/h14_secondary_cmux_materialization.md`
- `algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage89_h14_promotion_policy_integration/stage89_run.log`
- `repro/stage89_h14_promotion_policy_integration/current_smoke/summary.csv`
- `repro/stage89_h14_promotion_policy_integration/current_smoke/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage89_h14_promotion_policy_integration/current_smoke/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage89_h14_promotion_policy_integration/current_smoke/backend_pvw_target_SET_2_3_2048/build.log`
- `repro/stage89_h14_promotion_policy_integration/current_smoke/backend_pvw_target_SET_2_3_2048/run.log`
- `repro/stage89_h14_promotion_policy_integration/current_smoke/scalar_ternary_SET_2_3_2048/build.log`
- `repro/stage89_h14_promotion_policy_integration/summary.csv`

## Stage 90 External Claim Unlock

- `docs/stage90_external_claim_unlock_log.md`
- `experiments/stage90_external_claim_unlock_plan.md`
- `scripts/run_stage90_external_claim_unlock.sh`
- `scripts/build_stage90_external_claim_unlock.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage90_external_claim_unlock/summary.csv`
- `repro/stage90_external_claim_unlock/citation_probe/summary.csv`
- `repro/stage90_external_claim_unlock/citation_probe/access_probe.csv`
- `repro/stage90_external_claim_unlock/native_perf_gate/summary.csv`
- `repro/stage90_external_claim_unlock/native_perf_gate/environment.log`
- `repro/stage90_external_claim_unlock/native_perf_gate/perf_smoke.log`
- `repro/stage90_external_claim_unlock/citation_probe.log`
- `repro/stage90_external_claim_unlock/native_perf_gate.log`
- `repro/stage90_external_claim_unlock/external_evidence_intake.log`
- `repro/stage90_external_claim_unlock/stage90_builder.log`

## Stage 91 Final SAB Optimization Package

- `docs/stage91_final_sab_optimization_package.md`
- `experiments/stage91_final_package_plan.md`
- `scripts/run_stage91_final_package.sh`
- `scripts/build_stage91_final_package.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage91_final_package/summary.csv`
- `repro/stage91_final_package/performance_claims.csv`
- `repro/stage91_final_package/noise_resource_claims.csv`
- `repro/stage91_final_package/claim_boundary.csv`
- `repro/stage91_final_package/reproduction_commands.csv`
- `repro/stage91_final_package/artifact_index.csv`

## Stage 92 External Unlock Execution Packet

- `docs/stage92_external_unlock_execution_packet.md`
- `experiments/stage92_external_unlock_execution_plan.md`
- `scripts/run_stage92_external_unlock_execution_packet.sh`
- `scripts/build_stage92_external_unlock_execution_packet.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage92_external_unlock_execution/summary.csv`
- `repro/stage92_external_unlock_execution/lane_matrix.csv`
- `repro/stage92_external_unlock_execution/commands.csv`
- `repro/stage92_external_unlock_execution/acceptance_matrix.csv`
- `repro/stage92_external_unlock_execution/artifact_index.csv`

## Stage 93 External Lane Attempt

- `docs/stage93_external_lane_attempt_log.md`
- `experiments/stage93_external_lane_attempt_plan.md`
- `scripts/run_stage93_external_lane_attempt.sh`
- `scripts/build_stage93_external_lane_attempt.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage93_external_lane_attempt/summary.csv`
- `repro/stage93_external_lane_attempt/artifact_index.csv`
- `repro/stage93_external_lane_attempt/native_perf_gate/summary.csv`
- `repro/stage93_external_lane_attempt/native_perf_gate/environment.log`
- `repro/stage93_external_lane_attempt/native_perf_gate/perf_smoke.log`
- `repro/stage93_external_lane_attempt/native_perf_gate.log`
- `repro/stage93_external_lane_attempt/local_fulltext_search.csv`

## Stage 94 Local Frontier Audit

- `docs/stage94_local_frontier_audit_log.md`
- `experiments/stage94_local_frontier_audit_plan.md`
- `scripts/run_stage94_local_frontier_audit.sh`
- `scripts/build_stage94_local_frontier_audit.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage94_local_frontier_audit/summary.csv`
- `repro/stage94_local_frontier_audit/candidates.csv`
- `repro/stage94_local_frontier_audit/artifact_index.csv`

## Stage 95 Public Source Reprobe

- `docs/stage95_public_source_reprobe_log.md`
- `experiments/stage95_public_source_reprobe_plan.md`
- `scripts/run_stage95_public_source_reprobe.sh`
- `scripts/build_stage95_public_source_reprobe.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage95_public_source_reprobe/summary.csv`
- `repro/stage95_public_source_reprobe/route_matrix.csv`
- `repro/stage95_public_source_reprobe/artifact_index.csv`

## Stage 96 Upstream Delta Audit

- `docs/stage96_upstream_delta_audit_log.md`
- `experiments/stage96_upstream_delta_audit_plan.md`
- `scripts/run_stage96_upstream_delta_audit.sh`
- `scripts/build_stage96_upstream_delta_audit.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage96_upstream_delta_audit/summary.csv`
- `repro/stage96_upstream_delta_audit/delta_by_area.csv`
- `repro/stage96_upstream_delta_audit/delta_files.csv`
- `repro/stage96_upstream_delta_audit/commit_range.csv`
- `repro/stage96_upstream_delta_audit/flag_guard.csv`
- `repro/stage96_upstream_delta_audit/stage96_run.log`
- `repro/stage96_upstream_delta_audit/artifact_index.csv`
- `docs/stage97_source_delta_guard_log.md`
- `experiments/stage97_source_delta_guard_plan.md`
- `scripts/run_stage97_source_delta_guard.sh`
- `scripts/build_stage97_source_delta_guard.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage97_source_delta_guard/summary.csv`
- `repro/stage97_source_delta_guard/source_delta.csv`
- `repro/stage97_source_delta_guard/symbol_guard.csv`
- `repro/stage97_source_delta_guard/build_flag_guard.csv`
- `repro/stage97_source_delta_guard/smoke_evidence.csv`
- `repro/stage97_source_delta_guard/stage97_run.log`
- `repro/stage97_source_delta_guard/artifact_index.csv`
- `docs/stage98_current_smoke_refresh_log.md`
- `experiments/stage98_current_smoke_refresh_plan.md`
- `scripts/run_stage98_current_smoke_refresh.sh`
- `scripts/build_stage98_current_smoke_refresh.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage98_current_smoke_refresh/summary.csv`
- `repro/stage98_current_smoke_refresh/raw_smoke.csv`
- `repro/stage98_current_smoke_refresh/artifact_index.csv`
- `repro/stage98_current_smoke_refresh/stage98_run.log`
- `repro/stage98_current_smoke_refresh/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage98_current_smoke_refresh/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage98_current_smoke_refresh/active_pvw_target_SET_2_3_2048/build.log`
- `repro/stage98_current_smoke_refresh/active_pvw_target_SET_2_3_2048/run.log`
- `repro/stage98_current_smoke_refresh/backend_pvw_target_SET_2_3_2048/build.log`
- `repro/stage98_current_smoke_refresh/backend_pvw_target_SET_2_3_2048/run.log`
- `repro/stage98_current_smoke_refresh/scalar_ternary_SET_2_3_2048/build.log`

## Stage 99 External Blocker Reprobe

- `docs/current_codex_goal_sab_completion.md`
- `docs/stage99_external_blocker_reprobe_log.md`
- `experiments/stage99_external_blocker_reprobe_plan.md`
- `scripts/run_stage99_external_blocker_reprobe.sh`
- `scripts/build_stage99_external_blocker_reprobe.py`
- `hypotheses/hypothesis_register.yaml`
- `repro/stage99_external_blocker_reprobe/summary.csv`
- `repro/stage99_external_blocker_reprobe/route_matrix.csv`
- `repro/stage99_external_blocker_reprobe/local_fulltext_search.csv`
- `repro/stage99_external_blocker_reprobe/artifact_index.csv`
- `repro/stage99_external_blocker_reprobe/stage99_run.log`
- `repro/stage99_external_blocker_reprobe/native_perf_probe.log`
- `repro/stage99_external_blocker_reprobe/citation_probe.log`
- `repro/stage99_external_blocker_reprobe/native_perf_probe/summary.csv`
- `repro/stage99_external_blocker_reprobe/native_perf_probe/environment.log`
- `repro/stage99_external_blocker_reprobe/native_perf_probe/perf_smoke.log`
- `repro/stage99_external_blocker_reprobe/citation_probe/summary.csv`
- `repro/stage99_external_blocker_reprobe/citation_probe/access_probe.csv`
- `repro/stage38_fulltext_review_gate/summary.csv`
- `repro/stage38_fulltext_review_gate/review_checklist.csv`
- `repro/external_evidence_intake/summary.csv`

## Stage 100 Full-Text Anchor Prefill

- `docs/stage100_fulltext_anchor_prefill_log.md`
- `experiments/stage100_fulltext_anchor_prefill_plan.md`
- `scripts/run_stage100_fulltext_anchor_prefill.sh`
- `scripts/build_stage100_fulltext_anchor_prefill.py`
- `repro/stage100_fulltext_anchor_prefill/summary.csv`
- `repro/stage100_fulltext_anchor_prefill/page_keyword_hits.csv`
- `repro/stage100_fulltext_anchor_prefill/anchor_candidates.csv`
- `repro/stage100_fulltext_anchor_prefill/artifact_index.csv`
- `repro/stage100_fulltext_anchor_prefill/stage100_run.log`
- `repro/stage100_fulltext_anchor_prefill/stage100_build.log`
- `repro/stage38_fulltext_review_gate/review_checklist.csv`

## Stage 101 CB5 Remote Native Perf

- `docs/stage101_cb5_remote_native_perf_log.md`
- `experiments/stage101_cb5_remote_native_perf_plan.md`
- `scripts/build_stage101_cb5_remote_native_perf.py`
- `repro/stage101_cb5_remote_native_perf/summary.csv`
- `repro/stage101_cb5_remote_native_perf/counter_metrics.csv`
- `repro/stage101_cb5_remote_native_perf/artifact_index.csv`
- `repro/stage101_cb5_remote_native_perf/stage101_remote_env.log`
- `repro/stage101_cb5_remote_native_perf/stage28_native_perf_counter_gate/summary.csv`
- `repro/stage101_cb5_remote_native_perf/stage28_native_perf_counter_gate/bench_perf.log`
- `repro/stage101_cb5_remote_native_perf/stage28_native_perf_counter_gate/bench_run.log`
- `repro/stage101_cb5_remote_native_perf/attribution_probe/event_support.csv`
- `repro/stage101_cb5_remote_native_perf/attribution_probe/bench_attribution_perf.log`
- `repro/stage101_cb5_remote_native_perf/attribution_probe/bench_attribution_run.log`

## Stage 102 2025/686 Source-Anchor Review

- `docs/stage102_686_source_anchor_review_log.md`
- `experiments/stage102_686_source_anchor_review_plan.md`
- `scripts/build_stage102_686_source_anchor_review.py`
- `repro/stage102_686_source_anchor_review/summary.csv`
- `repro/stage102_686_source_anchor_review/review_matrix.csv`
- `repro/stage102_686_source_anchor_review/artifact_index.csv`
- `repro/stage38_fulltext_review_gate/review_checklist.csv`

## Stage 103 Related-Work And Novelty Review

- `docs/stage103_related_work_novelty_review_log.md`
- `experiments/stage103_related_work_novelty_review_plan.md`
- `scripts/build_stage103_related_work_novelty_review.py`
- `repro/stage103_related_work_novelty_review/summary.csv`
- `repro/stage103_related_work_novelty_review/related_work_matrix.csv`
- `repro/stage103_related_work_novelty_review/novelty_claim_matrix.csv`
- `repro/stage103_related_work_novelty_review/source_verification.csv`
- `repro/stage103_related_work_novelty_review/artifact_index.csv`

## Stage 104 Post-External Final Package

- `docs/stage104_post_external_final_package.md`
- `experiments/stage104_post_external_final_package_plan.md`
- `scripts/build_stage104_post_external_final_package.py`
- `repro/stage104_post_external_final_package/summary.csv`
- `repro/stage104_post_external_final_package/performance_claims.csv`
- `repro/stage104_post_external_final_package/claim_boundary.csv`
- `repro/stage104_post_external_final_package/evidence_bridge.csv`
- `repro/stage104_post_external_final_package/reproduction_commands.csv`
- `repro/stage104_post_external_final_package/artifact_index.csv`

## Stage 105 Goal Completion Audit

- `docs/stage105_goal_completion_audit.md`
- `experiments/stage105_goal_completion_audit_plan.md`
- `scripts/build_stage105_goal_completion_audit.py`
- `repro/stage105_goal_completion_audit/summary.csv`
- `repro/stage105_goal_completion_audit/requirement_matrix.csv`
- `repro/stage105_goal_completion_audit/claim_limit_matrix.csv`
- `repro/stage105_goal_completion_audit/artifact_index.csv`

## Stage 106 MAT-RLWE SAB Research Loop

- `docs/stage106_mat_rlwe_sab_research_loop.md`
- `experiments/stage106_mat_rlwe_sab_research_plan.md`
- `theory_checks/mat_rlwe_sab_amortized_optimality.md`
- `algorithm_variants/mat_rlwe_sab_rbody_optimal_path.md`
- `literature/mat_rlwe_sab_literature_axes.csv`
- `scripts/build_stage106_mat_rlwe_sab_research_loop.py`
- `repro/stage106_mat_rlwe_sab_research_loop/summary.csv`
- `repro/stage106_mat_rlwe_sab_research_loop/amortized_metric_table.csv`
- `repro/stage106_mat_rlwe_sab_research_loop/research_gate_matrix.csv`
- `repro/stage106_mat_rlwe_sab_research_loop/theory_bound_matrix.csv`
- `repro/stage106_mat_rlwe_sab_research_loop/candidate_variant_matrix.csv`
- `repro/stage106_mat_rlwe_sab_research_loop/artifact_index.csv`

## Stage 107 MAT Kernel Structure Audit

- `docs/stage107_mat_kernel_structure_audit.md`
- `scripts/build_stage107_mat_kernel_structure_audit.py`
- `repro/stage107_mat_kernel_structure_audit/summary.csv`
- `repro/stage107_mat_kernel_structure_audit/kernel_structure.csv`
- `repro/stage107_mat_kernel_structure_audit/next_gate.csv`
- `repro/stage107_mat_kernel_structure_audit/artifact_index.csv`
- `src/mosfhet/src/mattrgsw.c`

## Stage 108 Body-Major Layout Gate

- `docs/stage108_bodymajor_layout_gate.md`
- `experiments/stage108_bodymajor_layout_gate_plan.md`
- `scripts/run_stage108_bodymajor_layout_gate.sh`
- `scripts/build_stage108_bodymajor_layout_gate.py`
- `repro/stage108_bodymajor_layout_gate/summary.csv`
- `repro/stage108_bodymajor_layout_gate/kernel_comparison.csv`
- `repro/stage108_bodymajor_layout_gate/full_sab_smoke.csv`
- `repro/stage108_bodymajor_layout_gate/artifact_index.csv`
- `repro/stage108_bodymajor_layout_gate/tile4.log`
- `repro/stage108_bodymajor_layout_gate/fulltile.log`
- `repro/stage108_bodymajor_layout_gate/bodymajor.log`
- `src/mosfhet/Makefile.def`
- `src/mosfhet/src/mattrgsw.c`

## Stage 109 Body-Linear Invariant Gate

- `docs/stage109_body_linear_invariant_gate.md`
- `experiments/stage109_body_linear_invariant_gate_plan.md`
- `theory_checks/stage109_body_linear_external_product.md`
- `scripts/build_stage109_body_linear_invariant_gate.py`
- `repro/stage109_body_linear_invariant_gate/summary.csv`
- `repro/stage109_body_linear_invariant_gate/invariant_matrix.csv`
- `repro/stage109_body_linear_invariant_gate/operation_model.csv`
- `repro/stage109_body_linear_invariant_gate/artifact_index.csv`
- `src/mosfhet/include/mosfhet.h`
- `src/mosfhet/src/mattrgsw.c`
- `src/mosfhet/src/pvwtmlwe.c`

## Stage 110 r=6 Fulltile Complete-SAB Gate

- `docs/stage110_r6_fulltile_fullsab_gate.md`
- `experiments/stage110_r6_fulltile_fullsab_gate_plan.md`
- `scripts/run_stage110_r6_fulltile_fullsab_gate.sh`
- `scripts/build_stage110_r6_fulltile_fullsab_gate.py`
- `repro/stage110_r6_fulltile_fullsab_gate/summary.csv`
- `repro/stage110_r6_fulltile_fullsab_gate/comparison.csv`
- `repro/stage110_r6_fulltile_fullsab_gate/artifact_index.csv`
- `repro/stage110_r6_fulltile_fullsab_gate/tile4/summary.csv`
- `repro/stage110_r6_fulltile_fullsab_gate/tile4/run_0.log`
- `repro/stage110_r6_fulltile_fullsab_gate/fulltile/summary.csv`
- `repro/stage110_r6_fulltile_fullsab_gate/fulltile/run_0.log`

## Stage 111 r=6 Fulltile Repeated Gate

- `docs/stage111_r6_fulltile_repeated_gate.md`
- `experiments/stage111_r6_fulltile_repeated_gate_plan.md`
- `scripts/run_stage111_r6_fulltile_repeated_gate.sh`
- `scripts/build_stage111_r6_fulltile_repeated_gate.py`
- `repro/stage111_r6_fulltile_repeated_gate/summary.csv`
- `repro/stage111_r6_fulltile_repeated_gate/comparison.csv`
- `repro/stage111_r6_fulltile_repeated_gate/artifact_index.csv`
- `repro/stage111_r6_fulltile_repeated_gate/tile4/summary.csv`
- `repro/stage111_r6_fulltile_repeated_gate/tile4/run_0.log`
- `repro/stage111_r6_fulltile_repeated_gate/tile4/run_1.log`
- `repro/stage111_r6_fulltile_repeated_gate/tile4/run_2.log`
- `repro/stage111_r6_fulltile_repeated_gate/fulltile/summary.csv`
- `repro/stage111_r6_fulltile_repeated_gate/fulltile/run_0.log`
- `repro/stage111_r6_fulltile_repeated_gate/fulltile/run_1.log`
- `repro/stage111_r6_fulltile_repeated_gate/fulltile/run_2.log`

## Stage 112 Selector/Key-Format Gate

- `docs/stage112_selector_format_gate.md`
- `experiments/stage112_selector_format_gate_plan.md`
- `theory_checks/stage112_shared_mask_body_linear_counterexample.md`
- `algorithm_variants/mat_rlwe_sab_body_linear_selector_format.md`
- `scripts/build_stage112_selector_format_gate.py`
- `repro/stage112_selector_format_gate/summary.csv`
- `repro/stage112_selector_format_gate/shared_mask_counterexample.csv`
- `repro/stage112_selector_format_gate/candidate_format_matrix.csv`
- `repro/stage112_selector_format_gate/artifact_index.csv`

## Stage 113 r=2 Selector Simulator

- `docs/stage113_r2_selector_simulator.md`
- `experiments/stage113_r2_selector_simulator_plan.md`
- `theory_checks/stage113_lane_local_multimask_phase.md`
- `algorithm_variants/mat_rlwe_sab_r2_lane_local_multimask.md`
- `scripts/build_stage113_r2_selector_simulator.py`
- `repro/stage113_r2_selector_simulator/summary.csv`
- `repro/stage113_r2_selector_simulator/phase_simulation.csv`
- `repro/stage113_r2_selector_simulator/product_model.csv`
- `repro/stage113_r2_selector_simulator/artifact_index.csv`

## Stage 114 Lane-Local Resource Model

- `docs/stage114_lane_local_resource_model.md`
- `experiments/stage114_lane_local_resource_model_plan.md`
- `theory_checks/stage114_lane_local_resource_model.md`
- `scripts/build_stage114_lane_local_resource_model.py`
- `repro/stage114_lane_local_resource_model/summary.csv`
- `repro/stage114_lane_local_resource_model/resource_model.csv`
- `repro/stage114_lane_local_resource_model/artifact_index.csv`

## Stage 115 Lane-Local Toy C Gate

- `docs/stage115_lane_local_toy_c_gate.md`
- `experiments/stage115_lane_local_toy_c_gate_plan.md`
- `theory_checks/stage115_lane_local_toy_c_resource_gate.md`
- `algorithm_variants/mat_rlwe_sab_lane_local_toy_layout.md`
- `scripts/build_stage115_lane_local_toy_c_gate.py`
- `repro/stage115_lane_local_toy_c_gate/summary.csv`
- `repro/stage115_lane_local_toy_c_gate/toy_c_raw.csv`
- `repro/stage115_lane_local_toy_c_gate/layout_ratios.csv`
- `repro/stage115_lane_local_toy_c_gate/compile.log`
- `repro/stage115_lane_local_toy_c_gate/toy_lane_local_layout.c`
- `repro/stage115_lane_local_toy_c_gate/artifact_index.csv`

## Stage 116 Toy Arithmetic Equivalence

- `docs/stage116_toy_arithmetic_equivalence.md`
- `experiments/stage116_toy_arithmetic_equivalence_plan.md`
- `theory_checks/stage116_lane_local_arithmetic_equivalence.md`
- `algorithm_variants/mat_rlwe_sab_lane_local_arithmetic_model.md`
- `scripts/build_stage116_toy_arithmetic_equivalence.py`
- `repro/stage116_toy_arithmetic_equivalence/summary.csv`
- `repro/stage116_toy_arithmetic_equivalence/equivalence_results.csv`
- `repro/stage116_toy_arithmetic_equivalence/compile.log`
- `repro/stage116_toy_arithmetic_equivalence/toy_arithmetic_equivalence.c`
- `repro/stage116_toy_arithmetic_equivalence/artifact_index.csv`

## Stage 117 Selector Skeleton Gate

- `docs/stage117_selector_skeleton_gate.md`
- `experiments/stage117_selector_skeleton_gate_plan.md`
- `theory_checks/stage117_selector_skeleton_invariants.md`
- `algorithm_variants/mat_rlwe_sab_lane_local_selector_skeleton.md`
- `scripts/build_stage117_selector_skeleton_gate.py`
- `repro/stage117_selector_skeleton_gate/summary.csv`
- `repro/stage117_selector_skeleton_gate/selector_skeleton.csv`
- `repro/stage117_selector_skeleton_gate/compile.log`
- `repro/stage117_selector_skeleton_gate/selector_skeleton_gate.c`
- `repro/stage117_selector_skeleton_gate/artifact_index.csv`

## Stage 118 Real-Type Design Gate

- `docs/stage118_real_type_design_gate.md`
- `experiments/stage118_real_type_design_gate_plan.md`
- `theory_checks/stage118_real_type_noise_key_model.md`
- `algorithm_variants/mat_rlwe_sab_lane_local_real_type_design.md`
- `scripts/build_stage118_real_type_design_gate.py`
- `repro/stage118_real_type_design_gate/summary.csv`
- `repro/stage118_real_type_design_gate/type_layout.csv`
- `repro/stage118_real_type_design_gate/noise_key_model.csv`
- `repro/stage118_real_type_design_gate/compile.log`
- `repro/stage118_real_type_design_gate/real_type_design_gate.c`
- `repro/stage118_real_type_design_gate/artifact_index.csv`

## Stage 119 Shared-Term Object Gate

- `docs/stage119_shared_term_object_gate.md`
- `experiments/stage119_shared_term_object_gate_plan.md`
- `theory_checks/stage119_shared_term_semantics.md`
- `algorithm_variants/mat_rlwe_sab_vector_shared_lane_local_object.md`
- `scripts/build_stage119_shared_term_object_gate.py`
- `repro/stage119_shared_term_object_gate/summary.csv`
- `repro/stage119_shared_term_object_gate/phase_results.csv`
- `repro/stage119_shared_term_object_gate/object_layout.csv`
- `repro/stage119_shared_term_object_gate/compile.log`
- `repro/stage119_shared_term_object_gate/shared_term_object_gate.c`
- `repro/stage119_shared_term_object_gate/artifact_index.csv`

## Stage 120 Real Struct Phase/Noise Gate

- `docs/stage120_real_struct_phase_noise_gate.md`
- `experiments/stage120_real_struct_phase_noise_gate_plan.md`
- `theory_checks/stage120_real_struct_phase_noise_model.md`
- `algorithm_variants/mat_rlwe_sab_vector_shared_real_struct.md`
- `scripts/build_stage120_real_struct_phase_noise_gate.py`
- `repro/stage120_real_struct_phase_noise_gate/summary.csv`
- `repro/stage120_real_struct_phase_noise_gate/phase_noise_results.csv`
- `repro/stage120_real_struct_phase_noise_gate/layout_results.csv`
- `repro/stage120_real_struct_phase_noise_gate/compile.log`
- `repro/stage120_real_struct_phase_noise_gate/real_struct_phase_noise_gate.c`
- `repro/stage120_real_struct_phase_noise_gate/artifact_index.csv`

## Stage 121 Vector-Shared DFT/Conversion Gate

- `docs/stage121_vector_shared_dft_conversion_gate.md`
- `experiments/stage121_vector_shared_dft_conversion_gate_plan.md`
- `theory_checks/stage121_vector_shared_dft_conversion_model.md`
- `algorithm_variants/mat_rlwe_sab_vector_shared_dft_conversion.md`
- `scripts/build_stage121_vector_shared_dft_conversion_gate.py`
- `repro/stage121_vector_shared_dft_conversion_gate/summary.csv`
- `repro/stage121_vector_shared_dft_conversion_gate/conversion_results.csv`
- `repro/stage121_vector_shared_dft_conversion_gate/layout_results.csv`
- `repro/stage121_vector_shared_dft_conversion_gate/compile.log`
- `repro/stage121_vector_shared_dft_conversion_gate/vector_shared_dft_conversion_gate.c`
- `repro/stage121_vector_shared_dft_conversion_gate/artifact_index.csv`

## Stage 122 Structured EP Arithmetic Gate

- `docs/stage122_structured_ep_arithmetic_gate.md`
- `experiments/stage122_structured_ep_arithmetic_gate_plan.md`
- `theory_checks/stage122_structured_ep_arithmetic_model.md`
- `algorithm_variants/mat_rlwe_sab_vector_shared_structured_ep.md`
- `scripts/build_stage122_structured_ep_arithmetic_gate.py`
- `repro/stage122_structured_ep_arithmetic_gate/summary.csv`
- `repro/stage122_structured_ep_arithmetic_gate/arithmetic_results.csv`
- `repro/stage122_structured_ep_arithmetic_gate/layout_results.csv`
- `repro/stage122_structured_ep_arithmetic_gate/compile.log`
- `repro/stage122_structured_ep_arithmetic_gate/structured_ep_arithmetic_gate.c`
- `repro/stage122_structured_ep_arithmetic_gate/artifact_index.csv`

## Stage 123 Production FFT Smoke Gate

- `docs/stage123_production_fft_smoke_gate.md`
- `experiments/stage123_production_fft_smoke_gate_plan.md`
- `theory_checks/stage123_production_fft_smoke_model.md`
- `algorithm_variants/mat_rlwe_sab_vector_shared_production_fft_smoke.md`
- `scripts/build_stage123_production_fft_smoke_gate.py`
- `repro/stage123_production_fft_smoke_gate/summary.csv`
- `repro/stage123_production_fft_smoke_gate/smoke_results.csv`
- `repro/stage123_production_fft_smoke_gate/layout_results.csv`
- `repro/stage123_production_fft_smoke_gate/mosfhet_static_build.log`
- `repro/stage123_production_fft_smoke_gate/compile_probe.log`
- `repro/stage123_production_fft_smoke_gate/run_probe.log`
- `repro/stage123_production_fft_smoke_gate/production_fft_smoke_gate.c`
- `repro/stage123_production_fft_smoke_gate/artifact_index.csv`

## Stage 124 MOSFHET Type/API Skeleton

- `docs/stage124_mosfhet_type_api_skeleton.md`
- `experiments/stage124_mosfhet_type_api_skeleton_plan.md`
- `theory_checks/stage124_mosfhet_type_api_model.md`
- `algorithm_variants/mat_rlwe_sab_vector_shared_type_api_skeleton.md`
- `scripts/build_stage124_mosfhet_type_api_skeleton.py`
- `repro/stage124_mosfhet_type_api_skeleton/summary.csv`
- `repro/stage124_mosfhet_type_api_skeleton/api_results.csv`
- `repro/stage124_mosfhet_type_api_skeleton/layout_results.csv`
- `repro/stage124_mosfhet_type_api_skeleton/mosfhet_static_build.log`
- `repro/stage124_mosfhet_type_api_skeleton/compile_probe.log`
- `repro/stage124_mosfhet_type_api_skeleton/run_probe.log`
- `repro/stage124_mosfhet_type_api_skeleton/mosfhet_type_api_skeleton.c`
- `repro/stage124_mosfhet_type_api_skeleton/artifact_index.csv`

## Stage 125 Compact Selector Gadget Gate

- `docs/stage125_compact_selector_gadget_gate.md`
- `experiments/stage125_compact_selector_gadget_gate_plan.md`
- `theory_checks/stage125_compact_selector_gadget_model.md`
- `algorithm_variants/mat_rlwe_sab_compact_selector_gadget.md`
- `scripts/build_stage125_compact_selector_gadget_gate.py`
- `repro/stage125_compact_selector_gadget_gate/summary.csv`
- `repro/stage125_compact_selector_gadget_gate/gadget_results.csv`
- `repro/stage125_compact_selector_gadget_gate/layout_results.csv`
- `repro/stage125_compact_selector_gadget_gate/mosfhet_static_build.log`
- `repro/stage125_compact_selector_gadget_gate/compile_probe.log`
- `repro/stage125_compact_selector_gadget_gate/run_probe.log`
- `repro/stage125_compact_selector_gadget_gate/compact_selector_gadget_gate.c`
- `repro/stage125_compact_selector_gadget_gate/artifact_index.csv`

## Stage 126 Compact Selector Encryption/Noise Gate

- `docs/stage126_compact_selector_encryption_noise_gate.md`
- `experiments/stage126_compact_selector_encryption_noise_gate_plan.md`
- `theory_checks/stage126_compact_selector_encryption_noise_model.md`
- `algorithm_variants/mat_rlwe_sab_compact_selector_encryption_noise.md`
- `scripts/build_stage126_compact_selector_encryption_noise_gate.py`
- `repro/stage126_compact_selector_encryption_noise_gate/summary.csv`
- `repro/stage126_compact_selector_encryption_noise_gate/noise_results.csv`
- `repro/stage126_compact_selector_encryption_noise_gate/layout_results.csv`
- `repro/stage126_compact_selector_encryption_noise_gate/mosfhet_static_build.log`
- `repro/stage126_compact_selector_encryption_noise_gate/compile_probe.log`
- `repro/stage126_compact_selector_encryption_noise_gate/run_probe.log`
- `repro/stage126_compact_selector_encryption_noise_gate/compact_selector_encryption_noise_gate.c`
- `repro/stage126_compact_selector_encryption_noise_gate/artifact_index.csv`

## Stage 127 Isolated Compact EP Kernel Gate

- `docs/stage127_isolated_compact_ep_kernel_gate.md`
- `experiments/stage127_isolated_compact_ep_kernel_gate_plan.md`
- `theory_checks/stage127_isolated_compact_ep_kernel_model.md`
- `algorithm_variants/mat_rlwe_sab_isolated_compact_ep_kernel.md`
- `scripts/build_stage127_isolated_compact_ep_kernel_gate.py`
- `repro/stage127_isolated_compact_ep_kernel_gate/summary.csv`
- `repro/stage127_isolated_compact_ep_kernel_gate/kernel_results.csv`
- `repro/stage127_isolated_compact_ep_kernel_gate/mosfhet_static_build.log`
- `repro/stage127_isolated_compact_ep_kernel_gate/compile_probe.log`
- `repro/stage127_isolated_compact_ep_kernel_gate/run_probe.log`
- `repro/stage127_isolated_compact_ep_kernel_gate/isolated_compact_ep_kernel_gate.c`
- `repro/stage127_isolated_compact_ep_kernel_gate/artifact_index.csv`

## Stage 128 Compact EP API Boundary Gate

- `docs/stage128_compact_ep_api_boundary_gate.md`
- `experiments/stage128_compact_ep_api_boundary_gate_plan.md`
- `theory_checks/stage128_compact_ep_api_boundary_model.md`
- `algorithm_variants/mat_rlwe_sab_compact_ep_api_boundary.md`
- `scripts/build_stage128_compact_ep_api_boundary_gate.py`
- `repro/stage128_compact_ep_api_boundary_gate/summary.csv`
- `repro/stage128_compact_ep_api_boundary_gate/api_results.csv`
- `repro/stage128_compact_ep_api_boundary_gate/mosfhet_static_build.log`
- `repro/stage128_compact_ep_api_boundary_gate/compile_probe.log`
- `repro/stage128_compact_ep_api_boundary_gate/run_probe.log`
- `repro/stage128_compact_ep_api_boundary_gate/compact_ep_api_boundary_gate.c`
- `repro/stage128_compact_ep_api_boundary_gate/artifact_index.csv`

## Stage 129 Compact EP Microbench Gate

- `docs/stage129_compact_ep_microbench_gate.md`
- `experiments/stage129_compact_ep_microbench_gate_plan.md`
- `theory_checks/stage129_compact_ep_microbench_model.md`
- `algorithm_variants/mat_rlwe_sab_compact_ep_microbench.md`
- `scripts/build_stage129_compact_ep_microbench_gate.py`
- `repro/stage129_compact_ep_microbench_gate/summary.csv`
- `repro/stage129_compact_ep_microbench_gate/api_results.csv`
- `repro/stage129_compact_ep_microbench_gate/benchmark_samples.csv`
- `repro/stage129_compact_ep_microbench_gate/benchmark_aggregate.csv`
- `repro/stage129_compact_ep_microbench_gate/ratio_summary.csv`
- `repro/stage129_compact_ep_microbench_gate/mosfhet_static_build.log`
- `repro/stage129_compact_ep_microbench_gate/compile_probe.log`
- `repro/stage129_compact_ep_microbench_gate/run_probe.log`
- `repro/stage129_compact_ep_microbench_gate/compact_ep_microbench_gate.c`
- `repro/stage129_compact_ep_microbench_gate/artifact_index.csv`

## Stage 130 Shared-Source Compact EP Gate

- `docs/stage130_shared_source_compact_ep_gate.md`
- `experiments/stage130_shared_source_compact_ep_gate_plan.md`
- `theory_checks/stage130_shared_source_compact_ep_model.md`
- `algorithm_variants/mat_rlwe_sab_shared_source_compact_ep.md`
- `scripts/build_stage130_shared_source_compact_ep_gate.py`
- `repro/stage130_shared_source_compact_ep_gate/summary.csv`
- `repro/stage130_shared_source_compact_ep_gate/api_results.csv`
- `repro/stage130_shared_source_compact_ep_gate/benchmark_samples.csv`
- `repro/stage130_shared_source_compact_ep_gate/benchmark_aggregate.csv`
- `repro/stage130_shared_source_compact_ep_gate/ratio_summary.csv`
- `repro/stage130_shared_source_compact_ep_gate/mosfhet_static_build.log`
- `repro/stage130_shared_source_compact_ep_gate/compile_probe.log`
- `repro/stage130_shared_source_compact_ep_gate/run_probe.log`
- `repro/stage130_shared_source_compact_ep_gate/shared_source_compact_ep_gate.c`
- `repro/stage130_shared_source_compact_ep_gate/artifact_index.csv`

## Stage 131 Shared-Source Production API Gate

- `docs/stage131_shared_source_production_api_gate.md`
- `experiments/stage131_shared_source_production_api_gate_plan.md`
- `theory_checks/stage131_shared_source_production_api_model.md`
- `algorithm_variants/mat_rlwe_sab_shared_source_production_api.md`
- `scripts/build_stage131_shared_source_production_api_gate.py`
- `src/mosfhet/include/mosfhet.h`
- `src/mosfhet/src/mattrgsw.c`
- `repro/stage131_shared_source_production_api_gate/summary.csv`
- `repro/stage131_shared_source_production_api_gate/api_results.csv`
- `repro/stage131_shared_source_production_api_gate/mosfhet_static_build.log`
- `repro/stage131_shared_source_production_api_gate/compile_probe.log`
- `repro/stage131_shared_source_production_api_gate/run_probe.log`
- `repro/stage131_shared_source_production_api_gate/shared_source_production_api_gate.c`
- `repro/stage131_shared_source_production_api_gate/artifact_index.csv`

## Stage 132 Lane-Pair CMUX Consumption Gate

- `docs/stage132_lane_pair_cmux_consumption_gate.md`
- `experiments/stage132_lane_pair_cmux_consumption_gate_plan.md`
- `theory_checks/stage132_lane_pair_cmux_consumption_model.md`
- `algorithm_variants/mat_rlwe_sab_lane_pair_cmux_consumption.md`
- `scripts/build_stage132_lane_pair_cmux_consumption_gate.py`
- `repro/stage132_lane_pair_cmux_consumption_gate/summary.csv`
- `repro/stage132_lane_pair_cmux_consumption_gate/api_results.csv`
- `repro/stage132_lane_pair_cmux_consumption_gate/mosfhet_static_build.log`
- `repro/stage132_lane_pair_cmux_consumption_gate/compile_probe.log`
- `repro/stage132_lane_pair_cmux_consumption_gate/run_probe.log`
- `repro/stage132_lane_pair_cmux_consumption_gate/lane_pair_cmux_consumption_gate.c`
- `repro/stage132_lane_pair_cmux_consumption_gate/artifact_index.csv`

## Stage 133 Lane-State Closure Audit

- `docs/stage133_lane_state_closure_audit.md`
- `experiments/stage133_lane_state_closure_audit_plan.md`
- `theory_checks/stage133_lane_state_closure_model.md`
- `algorithm_variants/mat_rlwe_sab_lane_state_closure.md`
- `scripts/build_stage133_lane_state_closure_audit.py`
- `repro/stage133_lane_state_closure_audit/summary.csv`
- `repro/stage133_lane_state_closure_audit/closure_matrix.csv`
- `repro/stage133_lane_state_closure_audit/route_matrix.csv`
- `repro/stage133_lane_state_closure_audit/artifact_index.csv`

## Stage 134 Generalized Lane-Pair Input EP Gate

- `docs/stage134_generalized_lane_pair_input_ep_gate.md`
- `experiments/stage134_generalized_lane_pair_input_ep_gate_plan.md`
- `theory_checks/stage134_generalized_lane_pair_input_ep_model.md`
- `algorithm_variants/mat_rlwe_sab_generalized_lane_pair_input_ep.md`
- `scripts/build_stage134_generalized_lane_pair_input_ep_gate.py`
- `repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/api_results.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/benchmark_samples.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/benchmark_aggregate.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/ratio_summary.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/comparison_vs_stage130.csv`
- `repro/stage134_generalized_lane_pair_input_ep_gate/mosfhet_static_build.log`
- `repro/stage134_generalized_lane_pair_input_ep_gate/compile_probe.log`
- `repro/stage134_generalized_lane_pair_input_ep_gate/run_probe.log`
- `repro/stage134_generalized_lane_pair_input_ep_gate/generalized_lane_pair_input_ep_gate.c`
- `repro/stage134_generalized_lane_pair_input_ep_gate/artifact_index.csv`

## Stage 135 Decompose/DFT Reuse Target Gate

- `docs/stage135_decomp_dft_reuse_target_gate.md`
- `experiments/stage135_decomp_dft_reuse_target_gate_plan.md`
- `theory_checks/stage135_decomp_dft_reuse_target_model.md`
- `algorithm_variants/mat_rlwe_sab_decomp_dft_reuse_target.md`
- `scripts/build_stage135_decomp_dft_reuse_target_gate.py`
- `repro/stage135_decomp_dft_reuse_target_gate/summary.csv`
- `repro/stage135_decomp_dft_reuse_target_gate/target_matrix.csv`
- `repro/stage135_decomp_dft_reuse_target_gate/route_matrix.csv`
- `repro/stage135_decomp_dft_reuse_target_gate/artifact_index.csv`

## Stage 136 Batched Decompose/DFT Gate

- `docs/stage136_batched_decomp_dft_gate.md`
- `experiments/stage136_batched_decomp_dft_gate_plan.md`
- `theory_checks/stage136_batched_decomp_dft_model.md`
- `algorithm_variants/mat_rlwe_sab_batched_decomp_dft.md`
- `scripts/build_stage136_batched_decomp_dft_gate.py`
- `repro/stage136_batched_decomp_dft_gate/summary.csv`
- `repro/stage136_batched_decomp_dft_gate/correctness.csv`
- `repro/stage136_batched_decomp_dft_gate/benchmark_samples.csv`
- `repro/stage136_batched_decomp_dft_gate/benchmark_aggregate.csv`
- `repro/stage136_batched_decomp_dft_gate/ratio_summary.csv`
- `repro/stage136_batched_decomp_dft_gate/mosfhet_static_build.log`
- `repro/stage136_batched_decomp_dft_gate/compile_probe.log`
- `repro/stage136_batched_decomp_dft_gate/run_probe.log`
- `repro/stage136_batched_decomp_dft_gate/batched_decomp_dft_gate.c`
- `repro/stage136_batched_decomp_dft_gate/artifact_index.csv`

## Stage 137 Decompose/DFT Attribution Gate

- `docs/stage137_decomp_dft_attribution_gate.md`
- `experiments/stage137_decomp_dft_attribution_gate_plan.md`
- `theory_checks/stage137_decomp_dft_attribution_model.md`
- `algorithm_variants/mat_rlwe_sab_decomp_dft_attribution.md`
- `scripts/build_stage137_decomp_dft_attribution_gate.py`
- `repro/stage137_decomp_dft_attribution_gate/summary.csv`
- `repro/stage137_decomp_dft_attribution_gate/correctness.csv`
- `repro/stage137_decomp_dft_attribution_gate/benchmark_samples.csv`
- `repro/stage137_decomp_dft_attribution_gate/benchmark_aggregate.csv`
- `repro/stage137_decomp_dft_attribution_gate/attribution.csv`
- `repro/stage137_decomp_dft_attribution_gate/mosfhet_static_build.log`
- `repro/stage137_decomp_dft_attribution_gate/compile_probe.log`
- `repro/stage137_decomp_dft_attribution_gate/run_probe.log`
- `repro/stage137_decomp_dft_attribution_gate/decomp_dft_attribution_gate.c`
- `repro/stage137_decomp_dft_attribution_gate/artifact_index.csv`

## Stage 138 Shared-Mask Compact Gate

- `docs/stage138_shared_mask_compact_gate.md`
- `experiments/stage138_shared_mask_compact_gate_plan.md`
- `theory_checks/stage138_shared_mask_compact_model.md`
- `algorithm_variants/mat_rlwe_sab_shared_mask_compact.md`
- `scripts/build_stage138_shared_mask_compact_gate.py`
- `repro/stage138_shared_mask_compact_gate/summary.csv`
- `repro/stage138_shared_mask_compact_gate/correctness.csv`
- `repro/stage138_shared_mask_compact_gate/benchmark_samples.csv`
- `repro/stage138_shared_mask_compact_gate/benchmark_aggregate.csv`
- `repro/stage138_shared_mask_compact_gate/ratio_summary.csv`
- `repro/stage138_shared_mask_compact_gate/mosfhet_static_build.log`
- `repro/stage138_shared_mask_compact_gate/compile_probe.log`
- `repro/stage138_shared_mask_compact_gate/run_probe.log`
- `repro/stage138_shared_mask_compact_gate/shared_mask_compact_gate.c`
- `repro/stage138_shared_mask_compact_gate/artifact_index.csv`

## Stage 139 Compact Closure Audit

- `docs/stage139_compact_closure_audit.md`
- `experiments/stage139_compact_closure_audit_plan.md`
- `theory_checks/stage139_compact_closure_model.md`
- `algorithm_variants/mat_rlwe_sab_compact_closure_boundary.md`
- `scripts/build_stage139_compact_closure_audit.py`
- `repro/stage139_compact_closure_audit/summary.csv`
- `repro/stage139_compact_closure_audit/closure.csv`
- `repro/stage139_compact_closure_audit/mosfhet_static_build.log`
- `repro/stage139_compact_closure_audit/compile_probe.log`
- `repro/stage139_compact_closure_audit/run_probe.log`
- `repro/stage139_compact_closure_audit/compact_closure_audit.c`
- `repro/stage139_compact_closure_audit/artifact_index.csv`

## Stage 140 Closed Full-MAT Attribution Gate

- `docs/stage140_closed_fullmat_attribution_gate.md`
- `experiments/stage140_closed_fullmat_attribution_gate_plan.md`
- `theory_checks/stage140_closed_fullmat_attribution_model.md`
- `algorithm_variants/mat_rlwe_sab_closed_fullmat_attribution.md`
- `scripts/build_stage140_closed_fullmat_attribution_gate.py`
- `repro/stage140_closed_fullmat_attribution_gate/summary.csv`
- `repro/stage140_closed_fullmat_attribution_gate/correctness.csv`
- `repro/stage140_closed_fullmat_attribution_gate/benchmark_samples.csv`
- `repro/stage140_closed_fullmat_attribution_gate/benchmark_aggregate.csv`
- `repro/stage140_closed_fullmat_attribution_gate/attribution.csv`
- `repro/stage140_closed_fullmat_attribution_gate/mosfhet_static_build.log`
- `repro/stage140_closed_fullmat_attribution_gate/compile_probe.log`
- `repro/stage140_closed_fullmat_attribution_gate/run_probe.log`
- `repro/stage140_closed_fullmat_attribution_gate/closed_fullmat_attribution_gate.c`
- `repro/stage140_closed_fullmat_attribution_gate/artifact_index.csv`

## Stage 141 AVX512 Closed Full-MAT Gate

- `docs/stage141_avx512_closed_fullmat_gate.md`
- `experiments/stage141_avx512_closed_fullmat_gate_plan.md`
- `theory_checks/stage141_avx512_closed_fullmat_model.md`
- `algorithm_variants/mat_rlwe_sab_avx512_closed_fullmat.md`
- `scripts/build_stage141_avx512_closed_fullmat_gate.py`
- `repro/stage141_avx512_closed_fullmat_gate/summary.csv`
- `repro/stage141_avx512_closed_fullmat_gate/correctness.csv`
- `repro/stage141_avx512_closed_fullmat_gate/benchmark_samples.csv`
- `repro/stage141_avx512_closed_fullmat_gate/benchmark_aggregate.csv`
- `repro/stage141_avx512_closed_fullmat_gate/comparison.csv`
- `repro/stage141_avx512_closed_fullmat_gate/avx512_closed_fullmat_gate.c`
- `repro/stage141_avx512_closed_fullmat_gate/build_*.log`
- `repro/stage141_avx512_closed_fullmat_gate/compile_*.log`
- `repro/stage141_avx512_closed_fullmat_gate/run_*.log`
- `repro/stage141_avx512_closed_fullmat_gate/artifact_index.csv`
## Stage 142 AVX512 FMA-Order Fix Gate

- `docs/stage142_avx512_fma_order_fix_gate.md`
- `experiments/stage142_avx512_fma_order_fix_gate_plan.md`
- `theory_checks/stage142_avx512_fma_order_model.md`
- `algorithm_variants/mat_rlwe_sab_avx512_fma_order_fix.md`
- `scripts/build_stage142_avx512_fma_order_fix_gate.py`
- `repro/stage142_avx512_fma_order_fix_gate/summary.csv`
- `repro/stage142_avx512_fma_order_fix_gate/correctness.csv`
- `repro/stage142_avx512_fma_order_fix_gate/benchmark_samples.csv`
- `repro/stage142_avx512_fma_order_fix_gate/benchmark_aggregate.csv`
- `repro/stage142_avx512_fma_order_fix_gate/comparison.csv`
- `repro/stage142_avx512_fma_order_fix_gate/avx512_closed_fullmat_gate.c`
- `repro/stage142_avx512_fma_order_fix_gate/build_*.log`
- `repro/stage142_avx512_fma_order_fix_gate/compile_*.log`
- `repro/stage142_avx512_fma_order_fix_gate/run_*.log`
- `repro/stage142_avx512_fma_order_fix_gate/artifact_index.csv`
## Stage 143 Full SAB r4-Unrolled Smoke

- `docs/stage143_full_sab_r4_unrolled_smoke.md`
- `experiments/stage143_full_sab_r4_unrolled_smoke_plan.md`
- `theory_checks/stage143_full_sab_metric_model.md`
- `algorithm_variants/mat_rlwe_sab_r4_unrolled_full_sab_smoke.md`
- `scripts/build_stage143_full_sab_r4_unrolled_smoke.py`
- `repro/stage143_full_sab_r4_unrolled_smoke/summary.csv`
- `repro/stage143_full_sab_r4_unrolled_smoke/results.csv`
- `repro/stage143_full_sab_r4_unrolled_smoke/comparison.csv`
- `repro/stage143_full_sab_r4_unrolled_smoke/*_run_*.log`
- `repro/stage143_full_sab_r4_unrolled_smoke/artifact_index.csv`
## Stage 144 Full SAB Repeated r4-Unrolled Gate

- `docs/stage144_full_sab_repeated_r4_unrolled_gate.md`
- `experiments/stage144_full_sab_repeated_r4_unrolled_gate_plan.md`
- `theory_checks/stage144_repeated_full_sab_stat_model.md`
- `algorithm_variants/mat_rlwe_sab_r4_unrolled_repeated_gate.md`
- `scripts/build_stage144_full_sab_repeated_r4_unrolled_gate.py`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/summary.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_results.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_comparison.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/noise_results.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/noise_aggregate.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/resource_results.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/resource_comparison.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/*.log`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/artifact_index.csv`
## Stage 145 r4-Unrolled Policy Audit

- `docs/stage145_r4_unrolled_policy_audit.md`
- `experiments/stage145_r4_unrolled_policy_audit_plan.md`
- `theory_checks/stage145_policy_boundary.md`
- `scripts/build_stage145_r4_unrolled_policy_audit.py`
- `repro/stage145_r4_unrolled_policy_audit/summary.csv`
- `repro/stage145_r4_unrolled_policy_audit/policy.csv`
- `repro/stage145_r4_unrolled_policy_audit/artifact_index.csv`
- stage146_r4_unrolled_variance_attribution: `PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT`
  - `docs/stage146_r4_unrolled_variance_attribution.md`
  - `experiments/stage146_r4_unrolled_variance_attribution_plan.md`
  - `theory_checks/stage146_variance_model.md`
  - `repro/stage146_r4_unrolled_variance_attribution/`
- stage147_h14_r6_current_head_route: `PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT`
  - `docs/stage147_h14_r6_current_head_route.md`
  - `experiments/stage147_h14_r6_current_head_route_plan.md`
  - `theory_checks/stage147_h14_route_model.md`
  - `repro/stage147_h14_r6_current_head_route/`
- stage148_h14_r6_repeated_refresh: `PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE`
  - `docs/stage148_h14_r6_repeated_refresh.md`
  - `experiments/stage148_h14_r6_repeated_refresh_plan.md`
  - `theory_checks/stage148_h14_repeated_stat_model.md`
  - `repro/stage148_h14_r6_repeated_refresh/`
- stage149_h14_r6_claim_policy: `PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT`
  - `docs/stage149_h14_r6_claim_policy.md`
  - `experiments/stage149_h14_r6_claim_policy_plan.md`
  - `theory_checks/stage149_claim_boundary_model.md`
  - `repro/stage149_h14_r6_claim_policy/`
- stage150_final_package_refresh: `PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED`
  - `docs/stage150_final_package_refresh.md`
  - `experiments/stage150_final_package_refresh_plan.md`
  - `theory_checks/stage150_claim_scope_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage150_final_scope.md`
  - `repro/stage150_final_package_refresh/`
- stage151_h14_r6_fulltile_backend_smoke: `WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL`
  - `docs/stage151_h14_r6_fulltile_backend_smoke.md`
  - `experiments/stage151_h14_r6_fulltile_backend_smoke_plan.md`
  - `theory_checks/stage151_h14_r6_fulltile_backend_model.md`
  - `algorithm_variants/mat_rlwe_sab_h14_r6_fulltile_backend.md`
  - `repro/stage151_h14_r6_fulltile_backend_smoke/`
- stage152_dual_sub_kernel_gate: `PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE`
  - `docs/stage152_dual_sub_kernel_gate.md`
  - `experiments/stage152_dual_sub_kernel_gate_plan.md`
  - `theory_checks/stage152_dual_sub_kernel_model.md`
  - `algorithm_variants/mat_rlwe_sab_dual_sub_kernel.md`
  - `repro/stage152_dual_sub_kernel_gate/`
## stage153_dual_sub_fullsab_gate

- stage: Stage 153
- status: `NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED`
- root: `repro/stage153_dual_sub_fullsab_gate`
- index: `repro/stage153_dual_sub_fullsab_gate/artifact_index.csv`
## stage154_bodymajor_fullsab_closeout

- stage: Stage 154
- status: `REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER`
- root: `repro/stage154_bodymajor_fullsab_closeout`
- index: `repro/stage154_bodymajor_fullsab_closeout/artifact_index.csv`
- `repro/stage155_same_format_frontier_refresh/`: Stage155 profile-backed same-format frontier refresh outputs.
- `repro/stage156_lazy_dft_closure_gate/`: Stage156 lazy-DFT closure gate outputs.
- `repro/stage157_sub_decompose_fusion_preflight/`: Stage157 sub-decompose fusion preflight outputs.
- `repro/stage158_sub_decomp_fusion_fullsab_gate/`: Stage158 sub-decompose fusion full-SAB gate outputs.
- stage159_sub_decomp_fusion_repeated_gate: `PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE`
  - `docs/stage159_sub_decomp_fusion_repeated_gate.md`
  - `experiments/stage159_sub_decomp_fusion_repeated_gate_plan.md`
  - `theory_checks/stage159_sub_decomp_fusion_stat_model.md`
  - `algorithm_variants/mat_rlwe_sab_sub_decomp_fusion_repeated.md`
  - `repro/stage159_sub_decomp_fusion_repeated_gate/`
- stage160_post_fusion_frontier: `PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED`
  - `docs/stage160_post_fusion_frontier.md`
  - `experiments/stage160_post_fusion_frontier_plan.md`
  - `theory_checks/stage160_post_fusion_frontier_model.md`
  - `repro/stage160_post_fusion_frontier/`
- stage161_post_fusion_attribution: `PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED`
  - `docs/stage161_post_fusion_attribution.md`
  - `experiments/stage161_post_fusion_attribution_plan.md`
  - `theory_checks/stage161_post_fusion_attribution_model.md`
  - `repro/stage161_post_fusion_attribution/`
- stage162_materialization_count_feasibility: `PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED`
  - `docs/stage162_materialization_count_feasibility.md`
  - `experiments/stage162_materialization_count_feasibility_plan.md`
  - `theory_checks/stage162_materialization_count_model.md`
  - `repro/stage162_materialization_count_feasibility/`
- stage163_from_dft_batching_microbench: `NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED`
  - `docs/stage163_from_dft_batching_microbench.md`
  - `experiments/stage163_from_dft_batching_microbench_plan.md`
  - `theory_checks/stage163_from_dft_batching_model.md`
  - `algorithm_variants/mat_rlwe_sab_from_dft_batching_microbench.md`
  - `repro/stage163_from_dft_batching_microbench/`
- stage164_representation_closure_route: `PASS_STAGE164_REPRESENTATION_ROUTE_TO_CLOSED_FULL_MAT_STREAMING_GATE`
  - `docs/stage164_representation_closure_route.md`
  - `experiments/stage164_representation_closure_route_plan.md`
  - `theory_checks/stage164_representation_closure_model.md`
  - `algorithm_variants/mat_rlwe_sab_representation_closure_route.md`
  - `repro/stage164_representation_closure_route/`
- stage165_closed_fullmat_streaming_microbench: `REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX`
  - `docs/stage165_closed_fullmat_streaming_microbench.md`
  - `experiments/stage165_closed_fullmat_streaming_microbench_plan.md`
  - `theory_checks/stage165_closed_fullmat_streaming_model.md`
  - `algorithm_variants/mat_rlwe_sab_closed_fullmat_streaming.md`
  - `repro/stage165_closed_fullmat_streaming_microbench/`
- stage166_shared_output_compact_algebra_gate: `PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED`
  - `docs/stage166_shared_output_compact_algebra_gate.md`
  - `experiments/stage166_shared_output_compact_algebra_gate_plan.md`
  - `theory_checks/stage166_shared_output_compact_algebra_model.md`
  - `algorithm_variants/mat_rlwe_sab_shared_output_compact_algebra.md`
  - `repro/stage166_shared_output_compact_algebra_gate/`
- stage167_cb5_native_r6_counter_refresh: `PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED`
  - `docs/stage167_cb5_native_r6_counter_refresh.md`
  - `experiments/stage167_cb5_native_r6_counter_refresh_plan.md`
  - `theory_checks/stage167_native_counter_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_counter_current_r6.md`
  - `repro/stage167_cb5_native_r6_counter_refresh/`
- stage168_native_counter_frontier: `PASS_STAGE168_ROUTE_TO_NATIVE_REPEATED_AND_SPLIT_COUNTERS`
  - `docs/stage168_native_counter_frontier.md`
  - `experiments/stage168_native_counter_frontier_plan.md`
  - `theory_checks/stage168_counter_frontier_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_counter_frontier.md`
  - `repro/stage168_native_counter_frontier/`
- stage169_cb5_native_repeated_r6_gate: `PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE`
  - `docs/stage169_cb5_native_repeated_r6_gate.md`
  - `experiments/stage169_cb5_native_repeated_r6_gate_plan.md`
  - `theory_checks/stage169_native_repeated_stats_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_repeated_r6.md`
  - `repro/stage169_cb5_native_repeated_r6_gate/`
- stage170_native_split_counter_microbench: `PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED`
  - `docs/stage170_native_split_counter_microbench.md`
  - `experiments/stage170_native_split_counter_microbench_plan.md`
  - `theory_checks/stage170_split_counter_scope.md`
  - `algorithm_variants/mat_rlwe_sab_native_split_counter_microbench.md`
  - `repro/stage170_native_split_counter_microbench/`
- stage171_structured_compact_keygen_feasibility: `PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY`
  - `docs/stage171_structured_compact_keygen_feasibility.md`
  - `experiments/stage171_structured_compact_keygen_feasibility_plan.md`
  - `theory_checks/stage171_structured_compact_keygen_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_compact_keygen_feasibility.md`
  - `repro/stage171_structured_compact_keygen_feasibility/`
- stage172_frontier_closeout: `PASS_STAGE172_FRONTIER_CLOSEOUT_RECORDED`
  - `docs/stage172_frontier_closeout.md`
  - `experiments/stage172_frontier_closeout_plan.md`
  - `theory_checks/stage172_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_frontier_closeout.md`
  - `repro/stage172_frontier_closeout/`
- stage174_from_dft_direct_scale_gate: `NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED`
  - `docs/stage174_from_dft_direct_scale_gate.md`
  - `experiments/stage174_from_dft_direct_scale_gate_plan.md`
  - `theory_checks/stage174_direct_scale_model.md`
  - `algorithm_variants/mat_rlwe_sab_from_dft_direct_scale.md`
  - `repro/stage174_from_dft_direct_scale_gate/`
- stage175_post_stage174_frontier_refresh: `PASS_STAGE175_ROUTE_TO_STRUCTURED_COMPACT_TOY_GATE`
  - `docs/stage175_post_stage174_frontier_refresh.md`
  - `experiments/stage175_post_stage174_frontier_refresh_plan.md`
  - `theory_checks/stage175_route_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_post_stage174_frontier.md`
  - `repro/stage175_post_stage174_frontier_refresh/`
- stage173_structured_compact_phase_noise_toy: `PASS_STAGE173_PHASE_NOISE_TOY_PROOF_STILL_OPEN`
  - `docs/stage173_structured_compact_phase_noise_toy.md`
  - `experiments/stage173_structured_compact_phase_noise_toy_plan.md`
  - `theory_checks/stage173_structured_compact_phase_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_compact_phase_noise_toy.md`
  - `repro/stage173_structured_compact_phase_noise_toy/`
- stage176_structured_compact_security_api_gate: `BLOCK_STAGE176_STRUCTURED_COMPACT_SECURITY_API_NOT_CLOSED_REDIRECT_FULL_MAT`
  - `docs/stage176_structured_compact_security_api_gate.md`
  - `experiments/stage176_structured_compact_security_api_gate_plan.md`
  - `theory_checks/stage176_structured_compact_security_api_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_compact_security_api.md`
  - `repro/stage176_structured_compact_security_api_gate/`
- stage177_verified_literature_novelty_gate: `PASS_STAGE177_VERIFIED_LITERATURE_BOUNDARY_NO_STRONG_NOVELTY_CLAIM`
  - `docs/stage177_verified_literature_novelty_gate.md`
  - `experiments/stage177_verified_literature_novelty_gate_plan.md`
  - `theory_checks/stage177_literature_novelty_model.md`
  - `algorithm_variants/mat_rlwe_sab_literature_claim_boundary.md`
  - `repro/stage177_verified_literature_novelty_gate/`
- stage178_fullmat_perbit_frontier: `PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT`
  - `docs/stage178_fullmat_perbit_frontier.md`
  - `experiments/stage178_fullmat_perbit_frontier_plan.md`
  - `theory_checks/stage178_fullmat_perbit_frontier_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_fullmat_frontier.md`
  - `repro/stage178_fullmat_perbit_frontier/`
- stage179_mat_ep_microarch_audit: `PASS_STAGE179_AUDIT_SELECT_MAT_EP_SPLIT_PROBE_NO_CODE`
  - `docs/stage179_mat_ep_microarch_audit.md`
  - `experiments/stage179_mat_ep_microarch_audit_plan.md`
  - `theory_checks/stage179_mat_ep_microarch_model.md`
  - `algorithm_variants/mat_rlwe_sab_mat_ep_microarch_audit.md`
  - `repro/stage179_mat_ep_microarch_audit/`
- stage180_mat_ep_split_probe: `BLOCK_STAGE180_REMOTE_SETUP_OR_COMPILE_FAILED`
  - `docs/stage180_mat_ep_split_probe.md`
  - `experiments/stage180_mat_ep_split_probe_plan.md`
  - `theory_checks/stage180_mat_ep_split_probe_model.md`
  - `algorithm_variants/mat_rlwe_sab_mat_ep_split_probe.md`
  - `repro/stage180_mat_ep_split_probe/`
- stage181_sub_decomp_avx512_gate: `BLOCK_STAGE181_REMOTE_PIPELINE_FAILED`
  - `docs/stage181_sub_decomp_avx512_gate.md`
  - `experiments/stage181_sub_decomp_avx512_gate_plan.md`
  - `theory_checks/stage181_sub_decomp_avx512_model.md`
  - `algorithm_variants/mat_rlwe_sab_sub_decomp_avx512.md`
  - `repro/stage181_sub_decomp_avx512_gate/`
- stage182_exact_path_negative_frontier: `PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED`
  - `docs/stage182_exact_path_negative_frontier.md`
  - `experiments/stage182_exact_path_negative_frontier_plan.md`
  - `theory_checks/stage182_exact_path_negative_frontier_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_path_negative_frontier.md`
  - `repro/stage182_exact_path_negative_frontier/`
- stage183_addmul_dataflow_screen: `PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION`
  - `docs/stage183_addmul_dataflow_screen.md`
  - `experiments/stage183_addmul_dataflow_screen_plan.md`
  - `theory_checks/stage183_addmul_dataflow_model.md`
  - `algorithm_variants/mat_rlwe_sab_addmul_dataflow_screen.md`
  - `repro/stage183_addmul_dataflow_screen/`
- stage184_exact_route_closeout_claim_refresh: `PASS_STAGE184_EXACT_ROUTE_CLOSEOUT_CLAIM_REFRESH`
  - `docs/stage184_exact_route_closeout_claim_refresh.md`
  - `experiments/stage184_exact_route_closeout_claim_refresh_plan.md`
  - `theory_checks/stage184_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_route_closeout.md`
  - `repro/stage184_exact_route_closeout_claim_refresh/`
- stage185_research_repro_package_refresh: `PASS_STAGE185_RESEARCH_REPRO_PACKAGE_REFRESH`
  - `docs/stage185_research_repro_package_refresh.md`
  - `experiments/stage185_research_repro_package_refresh_plan.md`
  - `theory_checks/stage185_research_loop_gap_model.md`
  - `algorithm_variants/mat_rlwe_sab_research_program_snapshot.md`
  - `repro/stage185_research_repro_package_refresh/`
- stage186_compact_proof_unlock_audit: `BLOCK_STAGE186_COMPACT_PROOF_UNLOCK_NOT_READY`
  - `docs/stage186_compact_proof_unlock_audit.md`
  - `experiments/stage186_compact_proof_unlock_audit_plan.md`
  - `theory_checks/stage186_compact_proof_unlock_model.md`
  - `algorithm_variants/mat_rlwe_sab_compact_unlock_audit.md`
  - `repro/stage186_compact_proof_unlock_audit/`
- stage187_compact_proof_obligation_draft: `PASS_STAGE187_COMPACT_PROOF_DRAFT_IMPLEMENTATION_STILL_DENIED`
  - `docs/stage187_compact_proof_obligation_draft.md`
  - `experiments/stage187_compact_proof_obligation_draft_plan.md`
  - `theory_checks/stage187_compact_proof_obligations.md`
  - `algorithm_variants/mat_rlwe_sab_compact_proof_obligation_draft.md`
  - `repro/stage187_compact_proof_obligation_draft/`
- stage188_scoped_manuscript_skeleton: `PASS_STAGE188_SCOPED_MANUSCRIPT_SKELETON_READY`
  - `docs/stage188_scoped_manuscript_skeleton.md`
  - `experiments/stage188_scoped_manuscript_skeleton_plan.md`
  - `theory_checks/stage188_manuscript_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_scoped_manuscript_skeleton.md`
  - `repro/stage188_scoped_manuscript_skeleton/`
- stage189_closed_state_linear_probe: `PASS_STAGE189_T2_PUBLIC_CLOSURE_PROBE_DIRECT_SHARED_MASK_REJECTED`
  - `docs/stage189_closed_state_linear_probe.md`
  - `experiments/stage189_closed_state_linear_probe_plan.md`
  - `theory_checks/stage189_closed_state_linear_model.md`
  - `algorithm_variants/mat_rlwe_sab_closed_state_linear_probe.md`
  - `repro/stage189_closed_state_linear_probe/`
- stage190_selector_distribution_distinguisher: `PASS_STAGE190_T1_SELECTOR_DISTRIBUTION_DISTINGUISHERS_RECORDED_IMPLEMENTATION_STILL_DENIED`
  - `docs/stage190_selector_distribution_distinguisher.md`
  - `experiments/stage190_selector_distribution_distinguisher_plan.md`
  - `theory_checks/stage190_selector_distribution_model.md`
  - `algorithm_variants/mat_rlwe_sab_selector_distribution_distinguisher.md`
  - `repro/stage190_selector_distribution_distinguisher/`
- stage191_secret_correction_noise_resource_gate: `PASS_STAGE191_T4_SECRET_CORRECTION_LOWER_BOUND_RECORDED_IMPLEMENTATION_DENIED`
  - `docs/stage191_secret_correction_noise_resource_gate.md`
  - `experiments/stage191_secret_correction_noise_resource_gate_plan.md`
  - `theory_checks/stage191_secret_correction_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_secret_correction_closure.md`
  - `repro/stage191_secret_correction_noise_resource_gate/`
- stage192_compact_admission_route_selection: `PASS_STAGE192_COMPACT_IMPLEMENTATION_DENIED_ROUTE_EXACT_ADDMUL_PREFLIGHT`
  - `docs/stage192_compact_admission_route_selection.md`
  - `experiments/stage192_compact_admission_route_selection_plan.md`
  - `theory_checks/stage192_compact_admission_model.md`
  - `algorithm_variants/mat_rlwe_sab_compact_admission_route_selection.md`
  - `repro/stage192_compact_admission_route_selection/`
- stage193_exact_addmul_dataflow_preflight: `PASS_STAGE193_EXACT_ADDMUL_PREFLIGHT_NO_CODE_ROUTE_DFT_MECHANISM`
  - `docs/stage193_exact_addmul_dataflow_preflight.md`
  - `experiments/stage193_exact_addmul_dataflow_preflight_plan.md`
  - `theory_checks/stage193_exact_addmul_dataflow_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_addmul_dataflow_preflight.md`
  - `repro/stage193_exact_addmul_dataflow_preflight/`
- stage194_exact_dft_conversion_preflight: `PASS_STAGE194_EXACT_DFT_PREFLIGHT_NO_CODE_ROUTE_SCOPED_REFRESH`
  - `docs/stage194_exact_dft_conversion_preflight.md`
  - `experiments/stage194_exact_dft_conversion_preflight_plan.md`
  - `theory_checks/stage194_exact_dft_conversion_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_dft_conversion_preflight.md`
  - `repro/stage194_exact_dft_conversion_preflight/`
- stage195_scoped_paper_repro_refresh: `PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE`
  - `docs/stage195_scoped_paper_repro_refresh.md`
  - `experiments/stage195_scoped_paper_repro_refresh_plan.md`
  - `theory_checks/stage195_scoped_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_scoped_paper_repro_refresh.md`
  - `repro/stage195_scoped_paper_repro_refresh/`
- stage196_public_source_refresh: `PASS_STAGE196_PUBLIC_SOURCE_REFRESH_METADATA_VISIBLE_FULLTEXT_REVIEW_BLOCKED`
  - `docs/stage196_public_source_refresh.md`
  - `experiments/stage196_public_source_refresh_plan.md`
  - `theory_checks/stage196_citation_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_public_source_boundary.md`
  - `repro/stage196_public_source_refresh/`
- stage197_metadata_safe_citation_bank: `PASS_STAGE197_METADATA_SAFE_CITATION_BANK_READY_GOAL_ACTIVE`
  - `docs/stage197_metadata_safe_citation_bank.md`
  - `experiments/stage197_metadata_safe_citation_bank_plan.md`
  - `theory_checks/stage197_citation_support_model.md`
  - `algorithm_variants/mat_rlwe_sab_metadata_safe_writing_boundary.md`
  - `repro/stage197_metadata_safe_citation_bank/`
- stage198_metadata_safe_manuscript_refresh: `PASS_STAGE198_METADATA_SAFE_MANUSCRIPT_REFRESH_READY_GOAL_ACTIVE`
  - `docs/stage198_metadata_safe_manuscript_refresh.md`
  - `experiments/stage198_metadata_safe_manuscript_refresh_plan.md`
  - `theory_checks/stage198_manuscript_compliance_model.md`
  - `algorithm_variants/mat_rlwe_sab_metadata_safe_manuscript_refresh.md`
  - `repro/stage198_metadata_safe_manuscript_refresh/`
- stage199_active_goal_requirement_verifier: `PASS_STAGE199_ACTIVE_GOAL_VERIFIER_RECORDED_GOAL_ACTIVE`
  - `docs/stage199_active_goal_requirement_verifier.md`
  - `experiments/stage199_active_goal_requirement_verifier_plan.md`
  - `theory_checks/stage199_active_goal_completion_model.md`
  - `algorithm_variants/mat_rlwe_sab_active_goal_verifier.md`
  - `repro/stage199_active_goal_requirement_verifier/`
- stage200_formal_gap_model_with_probe: `PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE`
  - `docs/stage200_formal_gap_model_with_probe.md`
  - `experiments/stage200_formal_gap_model_with_probe_plan.md`
  - `theory_checks/stage200_rbody_gap_lower_bound_model.md`
  - `algorithm_variants/mat_rlwe_sab_formal_gap_model.md`
  - `repro/stage200_formal_gap_model_with_probe/`
- stage201_structured_selector_distribution_probe: `PASS_STAGE201_STRUCTURED_SELECTOR_DISTRIBUTION_PROBE_PROOF_ONLY`
  - `docs/stage201_structured_selector_distribution_probe.md`
  - `experiments/stage201_structured_selector_distribution_probe_plan.md`
  - `theory_checks/stage201_structured_selector_distribution_model.md`
  - `algorithm_variants/mat_rlwe_sab_structured_selector_distribution_probe.md`
  - `repro/stage201_structured_selector_distribution_probe/`
- stage202_dummy_padding_semantic_probe: `PASS_STAGE202_DUMMY_PADDING_SEMANTIC_PROBE_PROOF_ONLY`
  - `docs/stage202_dummy_padding_semantic_probe.md`
  - `experiments/stage202_dummy_padding_semantic_probe_plan.md`
  - `theory_checks/stage202_dummy_padding_semantic_model.md`
  - `algorithm_variants/mat_rlwe_sab_dummy_padding_semantic_probe.md`
  - `repro/stage202_dummy_padding_semantic_probe/`
- stage203_production_selector_equation_probe: `PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY`
  - `docs/stage203_production_selector_equation_probe.md`
  - `experiments/stage203_production_selector_equation_probe_plan.md`
  - `theory_checks/stage203_production_selector_equation_model.md`
  - `algorithm_variants/mat_rlwe_sab_production_selector_equation_probe.md`
  - `repro/stage203_production_selector_equation_probe/`

### Stage204 Source Anchor Intake

- `docs/stage204_source_anchor_intake.md`
- `experiments/stage204_source_anchor_intake_plan.md`
- `theory_checks/stage204_source_anchor_claim_boundary.md`
- `algorithm_variants/mat_rlwe_sab_source_anchor_policy.md`
- `repro/stage204_source_anchor_intake/`

### Stage205 Current Platform Probe

- `docs/stage205_current_platform_probe.md`
- `experiments/stage205_current_platform_probe_plan.md`
- `theory_checks/stage205_amortized_metric_and_platform_boundary.md`
- `algorithm_variants/mat_rlwe_sab_current_head_benchmark_policy.md`
- `repro/stage205_current_platform_probe/`

### Stage206 Current-Head High-Stat Evidence

- `docs/stage206_current_head_highstat.md`
- `experiments/stage206_current_head_highstat_plan.md`
- `theory_checks/stage206_statistical_claim_boundary.md`
- `algorithm_variants/mat_rlwe_sab_highstat_current_head_evidence.md`
- `repro/stage206_current_head_highstat/`
- stage207_current_head_resource_refresh:
  - `docs/stage207_current_head_resource_refresh.md`
  - `experiments/stage207_current_head_resource_refresh_plan.md`
  - `theory_checks/stage207_resource_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_current_head_resource_refresh.md`
  - `scripts/build_stage207_current_head_resource_refresh.py`
  - `repro/stage207_current_head_resource_refresh/`
- stage208_current_head_profile_refresh:
  - `docs/stage208_current_head_profile_refresh.md`
  - `experiments/stage208_current_head_profile_refresh_plan.md`
  - `theory_checks/stage208_profile_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_current_head_profile_refresh.md`
  - `scripts/run_stage208_current_head_profile_refresh.sh`
  - `scripts/build_stage208_current_head_profile_refresh.py`
  - `repro/stage208_current_head_profile_refresh/`
- stage209_current_head_mat_ep_split:
  - `docs/stage209_current_head_mat_ep_split.md`
  - `experiments/stage209_current_head_mat_ep_split_plan.md`
  - `theory_checks/stage209_current_head_mat_ep_split_model.md`
  - `algorithm_variants/mat_rlwe_sab_current_head_mat_ep_split.md`
  - `scripts/build_stage209_current_head_mat_ep_split.py`
  - `repro/stage209_current_head_mat_ep_split/`
- stage210_candidate_admission:
  - `docs/stage210_candidate_admission.md`
  - `experiments/stage210_candidate_admission_plan.md`
  - `theory_checks/stage210_candidate_admission_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage210_candidate_admission.md`
  - `scripts/build_stage210_candidate_admission.py`
  - `repro/stage210_candidate_admission/`
- stage211_fft_dataflow_preflight:
  - `docs/stage211_fft_dataflow_preflight.md`
  - `experiments/stage211_fft_dataflow_preflight_plan.md`
  - `theory_checks/stage211_fft_dataflow_preflight_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage211_fft_dataflow_preflight.md`
  - `scripts/build_stage211_fft_dataflow_preflight.py`
  - `repro/stage211_fft_dataflow_preflight/`
- stage212_multirow_fft_api_probe:
  - `docs/stage212_multirow_fft_api_probe.md`
  - `experiments/stage212_multirow_fft_api_probe_plan.md`
  - `theory_checks/stage212_multirow_fft_api_probe_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage212_multirow_fft_api_probe.md`
  - `scripts/build_stage212_multirow_fft_api_probe.py`
  - `repro/stage212_multirow_fft_api_probe/`
- stage213_dft_wrapper_integration_preflight:
  - `docs/stage213_dft_wrapper_integration_preflight.md`
  - `experiments/stage213_dft_wrapper_integration_preflight_plan.md`
  - `theory_checks/stage213_dft_wrapper_integration_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage213_dft_wrapper_integration_preflight.md`
  - `scripts/build_stage213_dft_wrapper_integration_preflight.py`
  - `repro/stage213_dft_wrapper_integration_preflight/`
- stage214_frontier_native_counter_handoff:
  - `docs/stage214_frontier_native_counter_handoff.md`
  - `experiments/stage214_frontier_native_counter_handoff_plan.md`
  - `theory_checks/stage214_frontier_counter_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage214_frontier_native_counter_handoff.md`
  - `scripts/build_stage214_frontier_native_counter_handoff.py`
  - `repro/stage214_frontier_native_counter_handoff/`
- stage215_native_counter_execution:
  - `docs/stage215_native_counter_execution.md`
  - `experiments/stage215_native_counter_execution_plan.md`
  - `theory_checks/stage215_counter_interpretation_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage215_native_counter_execution.md`
  - `scripts/build_stage215_native_counter_execution.py`
  - `repro/stage215_native_counter_execution/`
- stage216_post_counter_frontier:
  - `docs/stage216_post_counter_frontier.md`
  - `experiments/stage216_post_counter_frontier_plan.md`
  - `theory_checks/stage216_research_loop_frontier_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage216_post_counter_frontier.md`
  - `scripts/build_stage216_post_counter_frontier.py`
  - `repro/stage216_post_counter_frontier/`
- stage217_compact_keygen_security_preflight:
  - `docs/stage217_compact_keygen_security_preflight.md`
  - `experiments/stage217_compact_keygen_security_preflight_plan.md`
  - `theory_checks/stage217_compact_keygen_security_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage217_compact_keygen_security_preflight.md`
  - `scripts/build_stage217_compact_keygen_security_preflight.py`
  - `repro/stage217_compact_keygen_security_preflight/`
- stage218_compact_key_object_noise_prototype:
  - `docs/stage218_compact_key_object_noise_prototype.md`
  - `experiments/stage218_compact_key_object_noise_prototype_plan.md`
  - `theory_checks/stage218_compact_key_object_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage218_compact_key_object_noise_prototype.md`
  - `scripts/build_stage218_compact_key_object_noise_prototype.py`
  - `repro/stage218_compact_key_object_noise_prototype/`
- stage219_mosfhet_compact_key_api_skeleton:
  - `docs/stage219_mosfhet_compact_key_api_skeleton.md`
  - `experiments/stage219_mosfhet_compact_key_api_skeleton_plan.md`
  - `theory_checks/stage219_compact_key_api_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage219_compact_key_api_skeleton.md`
  - `scripts/build_stage219_mosfhet_compact_key_api_skeleton.py`
  - `repro/stage219_mosfhet_compact_key_api_skeleton/`
- stage220_encrypted_compact_keygen_prototype:
  - `docs/stage220_encrypted_compact_keygen_prototype.md`
  - `experiments/stage220_encrypted_compact_keygen_prototype_plan.md`
  - `theory_checks/stage220_encrypted_compact_keygen_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage220_encrypted_compact_keygen_prototype.md`
  - `scripts/build_stage220_encrypted_compact_keygen_prototype.py`
  - `repro/stage220_encrypted_compact_keygen_prototype/`
- stage221_compact_keygen_noise_recurrence:
  - `docs/stage221_compact_keygen_noise_recurrence.md`
  - `experiments/stage221_compact_keygen_noise_recurrence_plan.md`
  - `theory_checks/stage221_compact_keygen_noise_recurrence_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage221_compact_noise_recurrence.md`
  - `scripts/build_stage221_compact_keygen_noise_recurrence.py`
  - `repro/stage221_compact_keygen_noise_recurrence/`
- stage222_isolated_compact_ep_integration:
  - `docs/stage222_isolated_compact_ep_integration.md`
  - `experiments/stage222_isolated_compact_ep_integration_plan.md`
  - `theory_checks/stage222_isolated_compact_ep_integration_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage222_isolated_compact_ep.md`
  - `scripts/build_stage222_isolated_compact_ep_integration.py`
  - `repro/stage222_isolated_compact_ep_integration/`
- stage223_route_selection:
  - `docs/stage223_route_selection.md`
  - `experiments/stage223_route_selection_plan.md`
  - `theory_checks/stage223_route_selection_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage223_route_selection.md`
  - `scripts/build_stage223_route_selection.py`
  - `repro/stage223_route_selection/`
- stage224_exact_pvw_mat_avx_resource_refresh:
  - `docs/stage224_exact_pvw_mat_avx_resource_refresh.md`
  - `experiments/stage224_exact_pvw_mat_avx_resource_refresh_plan.md`
  - `theory_checks/stage224_exact_pvw_mat_avx_resource_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage224_exact_refresh.md`
  - `scripts/build_stage224_exact_pvw_mat_avx_resource_refresh.py`
  - `repro/stage224_exact_pvw_mat_avx_resource_refresh/`
- stage225_exact_refresh_noise_resource_rerun:
  - `docs/stage225_exact_refresh_noise_resource_rerun.md`
  - `experiments/stage225_exact_refresh_noise_resource_rerun_plan.md`
  - `theory_checks/stage225_exact_refresh_noise_resource_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage225_noise_resource.md`
  - `scripts/build_stage225_exact_refresh_noise_resource_rerun.py`
  - `repro/stage225_exact_refresh_noise_resource_rerun/`
- stage226_exact_mat_avx_counter_attribution:
  - `docs/stage226_exact_mat_avx_counter_attribution.md`
  - `experiments/stage226_exact_mat_avx_counter_attribution_plan.md`
  - `theory_checks/stage226_counter_attribution_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage226_counter_attribution.md`
  - `scripts/build_stage226_exact_mat_avx_counter_attribution.py`
  - `repro/stage226_exact_mat_avx_counter_attribution/`
- stage227_exact_route_claim_boundary_update:
  - `docs/stage227_exact_route_claim_boundary_update.md`
  - `experiments/stage227_exact_route_claim_boundary_update_plan.md`
  - `theory_checks/stage227_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage227_claim_boundary.md`
  - `scripts/build_stage227_exact_route_claim_boundary_update.py`
  - `repro/stage227_exact_route_claim_boundary_update/`
- stage228_counter_driven_backend_kernel_search:
  - `docs/stage228_counter_driven_backend_kernel_search.md`
  - `experiments/stage228_counter_driven_backend_kernel_search_plan.md`
  - `theory_checks/stage228_counter_driven_kernel_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage228_counter_driven_candidates.md`
  - `scripts/build_stage228_counter_driven_backend_kernel_search.py`
  - `repro/stage228_counter_driven_backend_kernel_search/`
- stage229_parameter_generalization_matrix:
  - `docs/stage229_parameter_generalization_matrix.md`
  - `experiments/stage229_parameter_generalization_matrix_plan.md`
  - `theory_checks/stage229_parameter_scope_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage229_parameter_scope.md`
  - `scripts/build_stage229_parameter_generalization_matrix.py`
  - `repro/stage229_parameter_generalization_matrix/`
- stage230_source_verified_literature_novelty_audit:
  - `docs/stage230_source_verified_literature_novelty_audit.md`
  - `experiments/stage230_source_verified_literature_novelty_audit_plan.md`
  - `theory_checks/stage230_novelty_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage230_literature_boundary.md`
  - `scripts/build_stage230_source_verified_literature_novelty_audit.py`
  - `repro/stage230_source_verified_literature_novelty_audit/`
- stage231_current_head_added_param_smoke:
  - `docs/stage231_current_head_added_param_refresh.md`
  - `experiments/stage231_current_head_added_param_refresh_plan.md`
  - `theory_checks/stage231_parameter_refresh_stats_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage231_current_head_added_params.md`
  - `scripts/build_stage231_current_head_added_param_refresh.py`
  - `repro/stage231_current_head_added_param_smoke/`
- stage232_selected_subset_fullstat_resource:
  - `docs/stage232_selected_subset_fullstat_resource.md`
  - `experiments/stage232_selected_subset_fullstat_resource_plan.md`
  - `theory_checks/stage232_subset_stats_resource_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage232_selected_subset.md`
  - `scripts/build_stage232_selected_subset_fullstat_resource.py`
  - `repro/stage232_selected_subset_fullstat_resource/`
- stage233_set_4_5_2048_r4_highstat_slice:
  - `docs/stage233_set_4_5_2048_r4_highstat_slice.md`
  - `experiments/stage233_set_4_5_2048_r4_highstat_slice_plan.md`
  - `theory_checks/stage233_highstat_slice_stats_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage233_highstat_slice.md`
  - `scripts/build_stage233_highstat_slice.py`
  - `repro/stage233_set_4_5_2048_r4_highstat_slice/`
- stage234_set_4_5_2048_r2_highstat_slice:
  - `docs/stage234_set_4_5_2048_r2_highstat_slice.md`
  - `experiments/stage234_set_4_5_2048_r2_highstat_slice_plan.md`
  - `theory_checks/stage234_highstat_slice_stats_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage234_highstat_slice.md`
  - `scripts/build_stage234_highstat_slice.py`
  - `repro/stage234_set_4_5_2048_r2_highstat_slice/`
- stage235_set_2_3_4096_r2_highstat_slice:
  - `docs/stage235_set_2_3_4096_r2_highstat_slice.md`
  - `experiments/stage235_set_2_3_4096_r2_highstat_slice_plan.md`
  - `theory_checks/stage235_highstat_slice_stats_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage235_highstat_slice.md`
  - `scripts/build_stage235_highstat_slice.py`
  - `repro/stage235_set_2_3_4096_r2_highstat_slice/`
- stage236_set_2_3_4096_r4_highstat_slice:
  - `docs/stage236_set_2_3_4096_r4_highstat_slice.md`
  - `experiments/stage236_set_2_3_4096_r4_highstat_slice_plan.md`
  - `theory_checks/stage236_selected_binary_matrix_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage236_selected_binary_matrix.md`
  - `scripts/build_stage236_highstat_slice.py`
  - `repro/stage236_set_2_3_4096_r4_highstat_slice/`
- stage237_scoped_manuscript_package:
  - `docs/stage237_scoped_manuscript_package.md`
  - `experiments/stage237_scoped_manuscript_package_plan.md`
  - `theory_checks/stage237_manuscript_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage237_scoped_manuscript.md`
  - `scripts/build_stage237_scoped_manuscript_package.py`
  - `repro/stage237_scoped_manuscript_package/`
- stage238_source_verified_citation_package:
  - `docs/stage238_source_verified_citation_package.md`
  - `experiments/stage238_source_verified_citation_package_plan.md`
  - `theory_checks/stage238_citation_claim_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage238_citation_package.md`
  - `scripts/build_stage238_source_verified_citation_package.py`
  - `repro/stage238_source_verified_citation_package/`
- stage239_bibtex_latex_stub:
  - `docs/stage239_bibtex_latex_stub.md`
  - `experiments/stage239_bibtex_latex_stub_plan.md`
  - `theory_checks/stage239_bibtex_policy_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage239_bibtex_stub.md`
  - `scripts/build_stage239_bibtex_latex_stub.py`
  - `references/stage239_pvw_mat_sab.bib`
  - `repro/stage239_bibtex_latex_stub/`
- stage240_scoped_latex_draft:
  - `docs/stage240_scoped_latex_draft.md`
  - `experiments/stage240_scoped_latex_draft_plan.md`
  - `theory_checks/stage240_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage240_scoped_draft.md`
  - `scripts/build_stage240_scoped_latex_draft.py`
  - `repro/stage240_scoped_latex_draft/`
- stage241_latex_compile_package:
  - `docs/stage241_latex_compile_package.md`
  - `experiments/stage241_latex_compile_package_plan.md`
  - `theory_checks/stage241_compile_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage241_compile_package.md`
  - `scripts/build_stage241_latex_compile_package.py`
  - `repro/stage241_latex_compile_package/`
- stage242_unresolved_bibtex_followup:
  - `docs/stage242_unresolved_bibtex_followup.md`
  - `experiments/stage242_unresolved_bibtex_followup_plan.md`
  - `theory_checks/stage242_bibtex_closure_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage242_bibtex_followup.md`
  - `scripts/build_stage242_unresolved_bibtex_followup.py`
  - `references/stage242_pvw_mat_sab.bib`
  - `repro/stage242_unresolved_bibtex_followup/`
- stage243_apply_lw_citations_recompile:
  - `docs/stage243_apply_lw_citations_recompile.md`
  - `experiments/stage243_apply_lw_citations_recompile_plan.md`
  - `theory_checks/stage243_draft_patch_claim_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage243_draft_patch.md`
  - `scripts/build_stage243_apply_lw_citations_recompile.py`
  - `repro/stage243_apply_lw_citations_recompile/`
- stage244_batchboot_bibtex_monitor:
  - `docs/stage244_batchboot_bibtex_monitor.md`
  - `experiments/stage244_batchboot_bibtex_monitor_plan.md`
  - `theory_checks/stage244_batchboot_citation_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage244_batchboot_monitor.md`
  - `scripts/build_stage244_batchboot_bibtex_monitor.py`
  - `repro/stage244_batchboot_bibtex_monitor/`
- stage245_current_head_counter_bridge:
  - `docs/stage245_current_head_counter_bridge.md`
  - `experiments/stage245_current_head_counter_bridge_plan.md`
  - `theory_checks/stage245_counter_reuse_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage245_counter_bridge.md`
  - `scripts/build_stage245_current_head_counter_bridge.py`
  - `repro/stage245_current_head_counter_bridge/`
- stage246_broader_algorithm_admission_gate:
  - `docs/stage246_broader_algorithm_admission_gate.md`
  - `experiments/stage246_broader_algorithm_admission_gate_plan.md`
  - `theory_checks/stage246_algorithm_admission_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage246_broader_algorithm_gate.md`
  - `scripts/build_stage246_broader_algorithm_admission_gate.py`
  - `repro/stage246_broader_algorithm_admission_gate/`
- stage248_structured_compact_finite_probe:
  - `docs/stage248_structured_compact_finite_probe.md`
  - `experiments/stage248_structured_compact_finite_probe_plan.md`
  - `theory_checks/stage248_structured_compact_finite_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage248_structured_compact_finite_probe.md`
  - `scripts/build_stage248_structured_compact_finite_probe.py`
  - `repro/stage248_structured_compact_finite_probe/`
- stage249_structured_compact_distribution_security:
  - `docs/stage249_structured_compact_distribution_security.md`
  - `experiments/stage249_structured_compact_distribution_security_plan.md`
  - `theory_checks/stage249_structured_compact_security_boundary.md`
  - `algorithm_variants/mat_rlwe_sab_stage249_structured_compact_security.md`
  - `scripts/build_stage249_structured_compact_distribution_security.py`
  - `repro/stage249_structured_compact_distribution_security/`
- stage250_exact_dense_lower_bound_gap:
  - `docs/stage250_exact_dense_lower_bound_gap.md`
  - `experiments/stage250_exact_dense_lower_bound_gap_plan.md`
  - `theory_checks/stage250_exact_dense_lower_bound_gap_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage250_exact_dense_lower_bound_gap.md`
  - `scripts/build_stage250_exact_dense_lower_bound_gap.py`
  - `repro/stage250_exact_dense_lower_bound_gap/`
- stage251_nonbinary_selector_semantics:
  - `docs/stage251_nonbinary_selector_semantics.md`
  - `experiments/stage251_nonbinary_selector_semantics_plan.md`
  - `theory_checks/stage251_nonbinary_selector_semantics_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage251_nonbinary_selector_semantics.md`
  - `scripts/build_stage251_nonbinary_selector_semantics.py`
  - `repro/stage251_nonbinary_selector_semantics/`
- stage252_nonbinary_mat_selector_key_skeleton:
  - `docs/stage252_nonbinary_mat_selector_key_skeleton.md`
  - `experiments/stage252_nonbinary_mat_selector_key_skeleton_plan.md`
  - `theory_checks/stage252_nonbinary_mat_selector_key_skeleton_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage252_nonbinary_mat_selector_key_skeleton.md`
  - `scripts/build_stage252_nonbinary_mat_selector_key_skeleton.py`
  - `repro/stage252_nonbinary_mat_selector_key_skeleton/`
- stage253_isolated_nonbinary_suba_equivalence:
  - `docs/stage253_isolated_nonbinary_suba_equivalence.md`
  - `experiments/stage253_isolated_nonbinary_suba_equivalence_plan.md`
  - `theory_checks/stage253_isolated_nonbinary_suba_equivalence_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage253_isolated_nonbinary_suba_equivalence.md`
  - `scripts/build_stage253_isolated_nonbinary_suba_equivalence.py`
  - `repro/stage253_isolated_nonbinary_suba_equivalence/`
- stage254_nonbinary_keygen_noise_preflight:
  - `docs/stage254_nonbinary_keygen_noise_preflight.md`
  - `experiments/stage254_nonbinary_keygen_noise_preflight_plan.md`
  - `theory_checks/stage254_nonbinary_keygen_noise_preflight_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage254_nonbinary_keygen_noise_preflight.md`
  - `scripts/build_stage254_nonbinary_keygen_noise_preflight.py`
  - `repro/stage254_nonbinary_keygen_noise_preflight/`
- stage255_mosfhet_nonbinary_selector_keygen_noise:
  - `docs/stage255_mosfhet_nonbinary_selector_keygen_noise.md`
  - `experiments/stage255_mosfhet_nonbinary_selector_keygen_noise_plan.md`
  - `theory_checks/stage255_mosfhet_nonbinary_selector_keygen_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage255_mosfhet_nonbinary_selector_keygen_noise.md`
  - `scripts/build_stage255_mosfhet_nonbinary_selector_keygen_noise.py`
  - `repro/stage255_mosfhet_nonbinary_selector_keygen_noise/`
- stage256_nonbinary_sparsemul_preflight:
  - `docs/stage256_nonbinary_sparsemul_preflight.md`
  - `experiments/stage256_nonbinary_sparsemul_preflight_plan.md`
  - `theory_checks/stage256_nonbinary_sparsemul_preflight_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage256_nonbinary_sparsemul_preflight.md`
  - `scripts/build_stage256_nonbinary_sparsemul_preflight.py`
  - `repro/stage256_nonbinary_sparsemul_preflight/`

- stage257_nonbinary_sparsemul_implementation:
  - `docs/stage257_nonbinary_sparsemul_implementation.md`
  - `experiments/stage257_nonbinary_sparsemul_implementation_plan.md`
  - `theory_checks/stage257_nonbinary_sparsemul_implementation_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage257_nonbinary_sparsemul.md`
  - `scripts/build_stage257_nonbinary_sparsemul_implementation.py`
  - `repro/stage257_nonbinary_sparsemul_implementation/`

- stage258_nonbinary_sparsemul_correctness_noise:
  - `docs/stage258_nonbinary_sparsemul_correctness_noise.md`
  - `experiments/stage258_nonbinary_sparsemul_correctness_noise_plan.md`
  - `theory_checks/stage258_nonbinary_sparsemul_noise_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage258_nonbinary_sparsemul_noise.md`
  - `scripts/build_stage258_nonbinary_sparsemul_correctness_noise.py`
  - `repro/stage258_nonbinary_sparsemul_correctness_noise/`

- stage259_nonbinary_full_sab_smoke:
  - `docs/stage259_nonbinary_full_sab_smoke.md`
  - `experiments/stage259_nonbinary_full_sab_smoke_plan.md`
  - `theory_checks/stage259_nonbinary_full_sab_scope.md`
  - `algorithm_variants/mat_rlwe_sab_stage259_nonbinary_full_sab.md`
  - `scripts/build_stage259_nonbinary_full_sab_smoke.py`
  - `repro/stage259_nonbinary_full_sab_smoke/`
