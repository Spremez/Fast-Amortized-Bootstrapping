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
  - `MOSFHET_DETERMINISTIC_RNG`
  - `MOSFHET_TEST_RNG_SEED`
- `src/mosfhet/include/mosfhet.h` PVW sample-array declaration
- `src/mosfhet/src/misc.c` deterministic test RNG path
- `scripts/run_stage6_seed_sweep.sh`
- `scripts/run_stage6_seed_sweep_range.sh`
- `scripts/run_stage7_bench_sweep.sh`

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

Repro artifacts:

- `repro/environment.md`
- `repro/baseline_registry.yaml`
- `repro/run_log.csv`
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
