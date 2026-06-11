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
- `src/mosfhet/include/mosfhet.h` PVW sample-array declaration

Documentation artifacts:

- `docs/roadmap_686_pvw_sab.md`
- `docs/mat_to_bootstrap_goal_audit.md`
- `docs/stage5_pvw_sparse_mul_log.md`
- `docs/stage5_pvw_bootstrap_wo_extract_log.md`
- `docs/stage5_pvw_extract_log.md`
- `docs/stage5_pvw_packing_hwks_log.md`
- `docs/stage5_pvw_full_bootstrap_log.md`
- `docs/stage5_pvw_rgsw_monomial_log.md`
- `docs/stage7_pvw_full_bench_log.md`

Repro artifacts:

- `repro/environment.md`
- `repro/baseline_registry.yaml`
- `repro/run_log.csv`
- `repro/reproduction_checklist.md`
