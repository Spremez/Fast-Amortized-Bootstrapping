# Stage159 Sub-Decompose Fusion Repeated Gate Plan

Date: 2026-07-03

## Objective

Upgrade the Stage158 one-run complete-SAB smoke into a strict research gate: repeated performance, final-output noise/correctness, and resource evidence.

## Primary Metric

`T_bootstrap/r`, implemented as `pvw_lane_avg_us`, is the primary amortized MAT-RLWE/SAB throughput metric.

## Variants

- Control: H14 r=6 backend path with active-buffer and backend FromDFT-add.
- Candidate: same flags plus `SAB_PVW_SUB_DECOMP_FUSION=true`.

## Gates

- Performance: paired repeated full-SAB A/B.
- Correctness/noise: deterministic multi-seed final-output comparison.
- Resource: key bytes, keygen per lane, internal VmHWM, and `/usr/bin/time` max RSS.

No default-path or paper-level claim is upgraded by this stage alone.
