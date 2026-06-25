# Stage 43 Post-Closure Current Smoke Plan

Date: 2026-06-26

## Goal

Refresh current-commit scalar/PVW build and correctness smoke evidence after
the Stage 42 evidence-closure audit.

Stage 43 is not a performance benchmark and does not upgrade any claim. It
only confirms that the current repository head still builds and runs the
baseline scalar path, the explicit PVW target gate, and the scalar non-binary
build guard.

## Command

```bash
STAGE33_OUT_DIR=repro/stage43_current_smoke_after_stage42 \
FFT_LIB=spqlios_avx512 \
bash scripts/run_stage33_current_smoke.sh
```

The command reuses the Stage 33 smoke runner with a distinct output directory
so historical Stage 33 artifacts are not overwritten.

## Gates

- scalar binary `SET_2_3_2048` full run ends with `Pass`;
- explicit PVW target full bootstrap gate reports
  `SAB_PVW target full bootstrap gate: Pass`;
- scalar ternary `SET_2_3_2048` build passes;
- results are recorded as current-state smoke only, not latency or paper
  evidence.

## Outputs

- `repro/stage43_current_smoke_after_stage42/summary.csv`
- `repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/build.log`
- `repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/run.log`
- `repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/build.log`
- `repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/run.log`
- `repro/stage43_current_smoke_after_stage42/scalar_ternary_SET_2_3_2048/build.log`

## Failure Handling

Any failed row blocks relying on current-head smoke evidence. Fix the build or
correctness issue before using later documentation or freeze artifacts as
current-state evidence.
