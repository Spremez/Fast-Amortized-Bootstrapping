# Stage84 H13 R6 Tile-Sweep Preflight Log

Date: 2026-06-26

## Purpose

Stage84 implements the Stage83-selected H13-C1 r=6 full-output tile
preflight behind `MAT_TRGSW_AVX512_R6_FULLTILE`. It does not change
scalar SAB, default `sab_pvw_*`, key format, or promoted r=2/r=4
behavior.

## Gates

| gate | status | metric | value | evidence | detail | next_action |
|---|---|---|---|---|---|---|
| stage84_inputs_available | PASS | stage83;tile4_log;fulltile_log | stage83=PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT; tile4=True; fulltile=True | repro/stage83_mat_body_design_check/decision.csv; repro/stage84_h13_r6_tile_sweep_preflight/tile4.log; repro/stage84_h13_r6_tile_sweep_preflight/fulltile.log | Stage84 has Stage83 preflight authorization and both kernel logs. | Restore missing inputs before interpreting Stage84. |
| stage84_kernel_correctness | PASS | tile4_correct;fulltile_correct | True;True | repro/stage84_h13_r6_tile_sweep_preflight/tile4.log; repro/stage84_h13_r6_tile_sweep_preflight/fulltile.log | Both tile4 and fulltile r>4 kernel identity-lane gates pass. | Do not use performance rows if correctness fails. |
| stage84_r6_kernel_comparison | PASS_KERNEL_POSITIVE | dft_output_ratio;full_output_ratio | 1.036;1.021 | repro/stage84_h13_r6_tile_sweep_preflight/kernel_comparison.csv | r=6 full-output tile beats tile4 in both DFT-output and full-output MAT microbench. | Run or interpret full-SAB smoke only as preflight; promotion still requires Stage85. |
| stage84_r8_guard | RECORDED_DIAGNOSTIC | dft_output_ratio;full_output_ratio | 0.981;1.029 | repro/stage84_h13_r6_tile_sweep_preflight/kernel_comparison.csv | r=8 remains on the existing tile4 dispatch under the fulltile flag; this is a diagnostic guard only. | Do not claim r=8 improvement from the r=6-only flag. |
| stage84_full_sab_smoke | NEUTRAL_OR_NEGATIVE_FULL_SAB | fulltile_vs_tile4 | 0.974 | repro/stage84_h13_r6_tile_sweep_preflight/full_sab_smoke.csv | r=6 complete-SAB smoke is not positive or was not run. | Proceed to Stage85 only if this gate is positive. |
| stage84_decision | PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED | promotion_policy |  | repro/stage84_h13_r6_tile_sweep_preflight/summary.csv | Stage84 kernel signal is positive but complete-SAB propagation is missing or neutral. | Do not promote; use Stage86 routing unless a stronger full-SAB gate is run. |

## Kernel Comparison

| bench | r | tile4 us | fulltile us | fulltile/tile4 | tile4 scalar speedup | fulltile scalar speedup |
|---|---:|---:|---:|---:|---:|---:|
| dft_output | 6 | 31.074 | 29.999 | 1.036 | 1.226 | 1.230 |
| dft_output | 8 | 45.133 | 46.014 | 0.981 | 1.161 | 1.079 |
| full_output | 6 | 45.086 | 44.173 | 1.021 | 1.417 | 1.425 |
| full_output | 8 | 70.040 | 68.053 | 1.029 | 1.283 | 1.199 |

## Full-SAB Smoke

| r | tile4 PVW us | fulltile PVW us | fulltile/tile4 | tile4 scalar speedup | fulltile scalar speedup |
|---:|---:|---:|---:|---:|---:|
| 6 | 39879943.000 | 40964582.000 | 0.974 | 1.392 | 1.328 |

## Decision

`PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED`

Stage84 is a preflight result only. A positive result must enter
Stage85 repeated complete-SAB, noise, and resource gates before any
promotion or bootstrapping-speedup claim changes.
