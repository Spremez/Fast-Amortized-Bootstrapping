# Stage84 H13 R6 Tile-Sweep Preflight Plan

Date: 2026-06-26

## Objective

Stage84 implements the Stage83-selected H13-C1 candidate as an explicit
preflight:

```text
MAT_TRGSW_AVX512_R6_FULLTILE=true
```

The flag tests whether the r=6 MAT body benefits from updating all seven
outputs in one coefficient block instead of using the current r>4 output tile
size of four. It does not change scalar SAB, default `sab_pvw_*`, key format,
or promoted r=2/r=4 behavior.

## Commands

```bash
STAGE84_OUT_DIR=repro/stage84_h13_r6_tile_sweep_preflight \
STAGE84_RUN_FULL_SAB=1 \
bash scripts/run_stage84_h13_r6_tile_sweep_preflight.sh
```

## Gates

- Kernel correctness:
  - `MAT_TRGSW/PVW r>4 kernel test: Pass` must appear in both tile4 and
    fulltile logs.
- Kernel microbench:
  - compare r=6 DFT-output and full-output MAT microbench for fulltile versus
    current `MAT_TRGSW_AVX512_RGT4_FUSED` tile4.
- Full-SAB smoke:
  - if kernel r=6 is positive, run one-run non-instrumented complete-SAB A/B
    for r=6 tile4 versus fulltile.
- Claim policy:
  - a positive Stage84 result opens Stage85 repeated/noise/resource gates only;
  - a neutral or negative result is recorded as an ablation and not promoted.

## Failure Handling

- Correctness failure: fail the stage and disable the flag before further
  testing.
- Kernel negative: record `PASS_STAGE84_H13_R6_TILE_SWEEP_NEGATIVE_NOT_PROMOTED`
  and return to Stage86 candidate routing.
- Kernel positive but full-SAB neutral: record kernel-only evidence and do not
  promote.
- Full-SAB positive: proceed to Stage85 repeated full-SAB/noise/resource gates.
