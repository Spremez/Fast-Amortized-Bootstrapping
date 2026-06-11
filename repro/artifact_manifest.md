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
