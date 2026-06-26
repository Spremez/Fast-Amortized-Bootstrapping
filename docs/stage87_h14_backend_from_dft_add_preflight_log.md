# Stage87 H14 Backend FromDFT-Add Preflight Log

Date: 2026-06-26

## Purpose

Stage87 implements the Stage86-selected H14-C1 backend materialization
preflight behind `SAB_PVW_BACKEND_FROM_DFT_ADD`. It compares the new
backend-level output conversion plus addend path against the existing
wrapper-level `pvmtmlwe_from_DFT_add` path under the same SAB flags.

## Full SAB Smoke

| variant | r | status | PVW us | scalar repeated us | speedup vs scalar | source |
|---|---:|---|---:|---:|---:|---|
| wrapper | 6 | Pass | 40196035.000 | 53309280.000 | 1.326 | repro/stage87_h14_backend_from_dft_add_preflight/full_sab_wrapper_r6/run_0.log |
| backend | 6 | Pass | 38284667.000 | 54762327.000 | 1.430 | repro/stage87_h14_backend_from_dft_add_preflight/full_sab_backend_r6/run_0.log |

## Gates

| gate | status | metric | value | evidence | detail |
|---|---|---|---:|---|---|
| stage87_explicit_flag | PASS_EXPLICIT_FLAG | flag | SAB_PVW_BACKEND_FROM_DFT_ADD | src/mosfhet/Makefile.def; src/mosfhet/src/pvwtmlwe.c; src/mosfhet/src/polynomial.c | Backend FromDFT-add path is behind an explicit opt-in flag. |
| stage87_correctness_smoke | PASS | kernel;target | True;True | repro/stage87_h14_backend_from_dft_add_preflight/kernel_run.log; repro/stage87_h14_backend_from_dft_add_preflight/target_run.log | Small staged gate and target full-output correctness gate pass. |
| stage87_full_sab_smoke | PASS_FULL_SAB_POSITIVE | backend_vs_wrapper_latency | 1.049925 | repro/stage87_h14_backend_from_dft_add_preflight/full_sab_smoke.csv | Backend-add r=6 one-run PVW latency 38284667.000 us versus wrapper 40196035.000 us. |
| stage87_decision | PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE | promotion_policy |  | repro/stage87_h14_backend_from_dft_add_preflight/summary.csv | Stage87 records H14-C1 as a promotion candidate, not a promoted/default path. |

## Decision

`PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE`.

This is still one-run smoke evidence. It does not promote the flag,
does not change scalar SAB, and does not justify a final bootstrapping
speedup claim until Stage88 repeated/noise/resource gates pass.
