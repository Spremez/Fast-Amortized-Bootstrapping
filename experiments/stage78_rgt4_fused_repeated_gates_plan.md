# Stage78 R>4 Fused Repeated Gates Plan

Date: 2026-06-26

## Goal

Stage78 tests whether the Stage77 H11 fused r>4 MAT kernel can move from a
positive smoke result to a repeatable full-SAB promotion candidate. The scalar
SAB path and the default r=2/r=4 PVW path remain unchanged.

## Hypothesis

H11 claims that a tiled fused MAT external-product path for r=6/r=8 can recover
the large-r throughput lost by the generic dense MAT loop. Stage77 showed
one-run evidence only. Stage78 must test the full bootstrapping path, not only
the kernel.

## Execution

Default command:

```bash
STAGE78_OUT_DIR=repro/stage78_rgt4_fused_repeated_gates \
  STAGE78_FULL_SAB_R6_RUNS=3 \
  STAGE78_FULL_SAB_R8_RUNS=1 \
  STAGE78_NOISE_SEED_COUNT=3 \
  bash scripts/run_stage78_rgt4_fused_repeated_gates.sh
```

The runner explicitly sets:

- `FFT_LIB=spqlios_avx512`
- `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`
- `MAT_TRGSW_AVX512_RGT4_FUSED=true`
- `SAB_PVW_ACTIVE_BUFFER_FUSION=true`

## Gates

| gate | requirement | failure handling |
|---|---|---|
| Stage77 precondition | Stage77 decision is `PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED`. | Stop and fix Stage77 evidence. |
| r=6 repeated full-SAB | At least 3 process samples, all correctness `Pass`, min speedup > 1.0. | Not promoted. |
| r=6 r4 boundary | Compare r=6 mean speedup against Stage36 r=4 mean and CI95 low. | If below r4 region, record as not promoted. |
| r=8 stress | At least one full-SAB sample with correctness `Pass` and speedup > 1.0. | Keep r=8 as diagnostic only. |
| final-output noise | r=6/r=8 zero PVW/scalar/pair failures. | Do not promote. |
| resource | PVW/scalar key, keygen, and RSS rows exist for r=6/r=8. | Do not promote until resource accounting is restored. |

## Claim Policy

Stage78 can only produce one of three local outcomes:

- promotion candidate requiring higher-stat confirmation;
- repeated evidence recorded but not promoted;
- failed/incomplete repeated gates.

It cannot by itself upgrade novelty, theorem-level 2025/686, native
perf-counter, or MAT-AVX512 theoretical-optimality claims.
