# Stage232 Experiment Plan

## Hypothesis

Changing scalar repeated SAB into exact dense PVW/MAT-SAB for `SET_2_3_4096`, r=4
should improve complete-SAB `T_bootstrap/r` over repeated scalar SAB because the
shared-mask MAT-RLWE state amortizes mask/key-flow work across r body lanes.

Status labels:

- [experiment checked, preflight only]: 3-run complete-SAB A/B and 3-seed noise
  have been executed.
- [statistical evidence insufficient]: n=3 and seeds=3 are not final paper
  statistics.
- [theory not closed]: this does not prove MAT-RLWE SAB optimality.

## Baseline

Repeated scalar SAB under the same `KEY=BINARY`, `PARAM=SET_2_3_4096`,
`FFT_LIB=spqlios_avx512`, `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and
`SAB_PVW_ACTIVE_BUFFER_FUSION=true` configuration.

## Primary Metric

Complete-SAB `T_bootstrap/r`, reported as speedup versus repeated scalar SAB.

## Commands

See `repro/stage232_selected_subset_fullstat_resource/reproduction_commands.md`.

## Promotion Gate

To promote added parameters into a main claim table, rerun at least 10
complete-SAB A/B runs and 20 noise seeds for the selected parameter matrix, with
resource/keygen/RSS recorded.
