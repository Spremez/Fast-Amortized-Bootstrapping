# Stage 33 Current Commit Smoke Plan

Date: 2026-06-26

## Objective

Refresh the current-commit build/correctness smoke after the Stage 27-32
evidence and orchestration work. This checks that the scalar baseline and the
explicit PVW target gate still run.

This stage is not a performance benchmark and must not be used as a speedup
claim.

## Command

```bash
bash scripts/run_stage33_current_smoke.sh
```

Default configuration:

```text
FFT_LIB=spqlios_avx512
PARAM=SET_2_3_2048
KEY=BINARY for scalar/PVW target runs
KEY=TERNARY for scalar build-only guard
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

## Gates

- scalar binary default run must print final `Pass`;
- explicit `SAB_PVW_TARGET_TEST` must print
  `SAB_PVW target full bootstrap gate: Pass`;
- scalar ternary build must pass, proving the PVW binary-only guard did not
  break the scalar non-binary build path.

## Output

```text
repro/stage33_current_smoke/summary.csv
repro/stage33_current_smoke/scalar_binary_SET_2_3_2048/build.log
repro/stage33_current_smoke/scalar_binary_SET_2_3_2048/run.log
repro/stage33_current_smoke/pvw_target_SET_2_3_2048/build.log
repro/stage33_current_smoke/pvw_target_SET_2_3_2048/run.log
repro/stage33_current_smoke/scalar_ternary_SET_2_3_2048/build.log
```
