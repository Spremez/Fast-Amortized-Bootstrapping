# Stage 25 Correctness, Noise, and Resource Matrix Plan

Date: 2026-06-25

## Objective

Convert the current best explicit PVW/MAT-SAB path into robust engineering
evidence:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
```

Stage 21, Stage 23, and Stage 24 are not promoted. They remain ablations or
deferred work.

## Matrix

Required scope:

- `r in {1,2,4}`;
- deterministic final-output correctness/noise;
- stage-level PVW-vs-scalar noise boundaries;
- key size, keygen time, internal HWM, and `/usr/bin/time` max RSS;
- scalar repeated baseline preserved as the comparison target.

## Commands

Final-output seed sweep smoke:

```bash
STAGE25_FINAL_NOISE_SEED_COUNT=3 \
STAGE25_FINAL_NOISE_R_VALUES="1 2 4" \
STAGE25_FINAL_NOISE_OUT_DIR=repro/stage25_final_noise_avx512_seeds3 \
bash scripts/run_stage25_final_noise_sweep.sh
```

Stage-level noise smoke:

```bash
STAGE25_STAGE_NOISE_R_VALUES="1 2 4" \
STAGE25_STAGE_NOISE_OUT_DIR=repro/stage25_stage_noise_avx512_trials1 \
bash scripts/run_stage25_stage_noise_probe.sh
```

Resource matrix:

```bash
STAGE25_RESOURCE_R_VALUES="1 2 4" \
STAGE25_RESOURCE_OUT_DIR=repro/stage25_resource_avx512 \
bash scripts/run_stage25_resource_matrix.sh
```

## Promotion Rule

Smoke-level Stage 25 evidence can mark the current path as
`stage25_initial_supported`, but not paper-grade.

To claim final robust engineering evidence, extend the final-output seed sweep
to at least 50 seeds for the promoted `r` values and keep zero PVW, scalar, and
pair failures under the same backend and target parameters.

Any resource overhead must be reported together with speedup. A throughput
claim must not imply keygen, key-size, or memory improvement unless the resource
matrix supports it.
