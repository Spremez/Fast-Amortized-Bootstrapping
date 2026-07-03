# MAT-RLWE SAB Dual-Sub Kernel Candidate

Date: 2026-07-03

## Candidate

`H76`: shared-input dual subtraction for adjacent direct/NCMUX butterfly updates inside PVW/MAT-SAB.

## Baseline

Two independent `pvmtmlwe_sub`-equivalent AVX512 loops over a k=1,r=6,N=2048 PVW_TMLWE sample.

## Candidate Delta

One AVX512 loop computes both outputs while loading the shared sample once.

## Current Status

`PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE`
