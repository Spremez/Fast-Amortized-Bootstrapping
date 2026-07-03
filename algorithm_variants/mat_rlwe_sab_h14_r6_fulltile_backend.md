# MAT-RLWE SAB H14 r=6 Backend Fulltile Candidate

Date: 2026-07-03

## Definition

Candidate `H75`: explicit `sab_pvw_*` full bootstrapping with:

- r=6 independent MAT-RLWE/PVW body lanes;
- binary `SET_2_3_2048`;
- active-buffer sparse schedule;
- backend FromDFT-add;
- r=6 fulltile MAT external-product AVX512 layout;
- scalar/default SAB unchanged.

## Baseline

The direct baseline is the same explicit backend path with the existing r>4 tile4 layout. The paper-level scalar baseline remains repeated scalar SAB measured per lane.
