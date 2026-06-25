# Stage 22 MAT-Aware AVX512 Limit Audit Plan

Date: 2026-06-25

## Objective

Answer whether the current MAT-aware AVX512 external product is close to its
useful theoretical limit for the target PVW/MAT-SAB path, or whether more
r-specific register tiling and layout work is justified.

This stage compares two same-backend implementations:

```text
generic:      FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=false
specialized:  FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
```

Both variants use the same scalar reference and the same complete SAB harness.

## Gates

Correctness:

- staged `SAB_PVW_KERNEL_TEST=true` must pass for both variants;
- full target SAB correctness must pass for any full-SAB smoke.

Microbench:

- collect `MAT_TRGSW vs scalar` and `MAT_TRGSW_FULL vs scalar_full`;
- collect `EP_BREAKDOWN` for decompose, DFT, and multiply phases;
- collect objdump counts for FMA-family and vector-move instructions.

Full SAB:

- run Stage 20 active-buffer full SAB with each MAT variant;
- treat one-run full SAB as smoke only;
- require repeated full SAB sweeps before promoting any stronger claim.

## Primary Command

```bash
STAGE22_KERNEL_RUNS=1 \
STAGE22_FULL_SAB_RUNS=1 \
STAGE22_FULL_SAB_R_VALUES="2 4" \
STAGE22_OUT_DIR=repro/stage22_mat_avx512_limit_audit_runs1_full1 \
bash scripts/run_stage22_mat_avx512_limit_audit.sh
```

## Expected Interpretation

If specialized improves kernel microbench but not full SAB, the claim remains a
kernel-level implementation gain. If full SAB also improves, the result still
needs repeated runs and noise/resource gates before it can be promoted.

If generic and specialized are close, Stage 22 should deprioritize further
small-r AVX512 work and move to Stage 23 schedule fusion.
