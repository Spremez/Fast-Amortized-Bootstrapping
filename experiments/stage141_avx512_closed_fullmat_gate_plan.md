# Stage141 AVX512 Closed Full-MAT Gate Plan

Date: 2026-07-03

## Objective

Compare existing closed full-MAT AVX512 variants under the same `spqlios_avx512` backend for the target shape `r=4,T=1,Bg=23,N=1024/2048`.

## Falsification Criteria

- any AVX512 config fails correctness;
- generic and specialized variants use different FFT backends;
- speedup is reported outside the target closed full-MAT shape;
- kernel speedup is claimed as complete SAB speedup without full SAB rerun.
