# Stage76 R>4 Kernel Feasibility Plan

Date: 2026-06-26

## Goal

Check whether the existing MAT external-product implementation is a viable
starting point for r>4 PVW/MAT-SAB optimization, after Stage74/75 showed that
direct r=6/r=8 lane-count expansion does not beat the promoted r=4 path.

This stage is diagnostic. It does not promote a new SAB path and does not
change scalar `sab_rlwe_bootstrap`, the default `sab_pvw_*` path, or the MAT
key format.

## Command

```bash
make clean
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_RGT4_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage76_rgt4_kernel_feasibility/rgt4_kernel_smoke.log
python scripts/build_stage76_rgt4_kernel_feasibility.py
```

## Correctness Gate

- `MAT_TRGSW/PVW r>4 kernel test: Pass` must appear in the raw log.
- The test must cover r=6 and r=8 identity-lane checks.

## Performance Gate

- Parse DFT-output `MAT_TRGSW vs scalar` for r=6/r=8.
- Parse full-output `MAT_TRGSW_FULL vs scalar_full` for r=6/r=8.
- Parse `EP_BREAKDOWN` for scalar repeated and MAT shared-mask modes.

Promotion requires DFT-output MAT speedup above repeated scalar for both r=6
and r=8, and full-output evidence with enough margin to justify complete-SAB
work. If DFT-output is negative and full-output is only low-margin positive,
record the result as diagnostic only.

## Failure Handling

- If correctness fails, stop all r>4 kernel analysis and fix the generic MAT
  path before any layout work.
- If DFT-output is negative, do not promote current r>4 MAT kernel scaling.
- If the MAT shared-mask breakdown is multiply dominated, route future work to
  a fused MAT multiply/layout/register-blocking hypothesis.

## Expected Output

- `repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv`
- `repro/stage76_rgt4_kernel_feasibility/ep_breakdown.csv`
- `repro/stage76_rgt4_kernel_feasibility/summary.csv`
- `docs/stage76_rgt4_kernel_feasibility_log.md`
