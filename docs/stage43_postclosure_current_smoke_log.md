# Stage 43 Post-Closure Current Smoke Log

Date: 2026-06-26

## Purpose

Stage 43 refreshes current-head scalar/PVW smoke evidence after the Stage 42
closure audit. It does not change scalar SAB, does not change `sab_pvw_*`, and
does not provide a performance claim.

## Command

```bash
STAGE33_OUT_DIR=repro/stage43_current_smoke_after_stage42 \
FFT_LIB=spqlios_avx512 \
bash scripts/run_stage33_current_smoke.sh
```

The run was launched from PowerShell through WSL:

```powershell
wsl -e bash -lc 'cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping && STAGE33_OUT_DIR=repro/stage43_current_smoke_after_stage42 FFT_LIB=spqlios_avx512 bash scripts/run_stage33_current_smoke.sh'
```

## Result

| gate | backend | key | param | status | evidence |
|---|---|---|---|---|---|
| scalar binary full run | `spqlios_avx512` | `BINARY` | `SET_2_3_2048` | PASS | `repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/run.log` |
| PVW target full gate | `spqlios_avx512` | `BINARY` | `SET_2_3_2048` | PASS | `repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/run.log` |
| scalar ternary build | `spqlios_avx512` | `TERNARY` | `SET_2_3_2048` | PASS | `repro/stage43_current_smoke_after_stage42/scalar_ternary_SET_2_3_2048/build.log` |

## Decision

The current repository head preserves the scalar baseline smoke path, the
explicit PVW target correctness gate, and the scalar non-binary build guard.
This is current-state build/correctness evidence only; it does not alter the
Stage 42 scoped-ready/stronger-blocked conclusion.
