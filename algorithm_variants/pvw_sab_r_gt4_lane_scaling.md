# Candidate Variant: PVW-SAB Direct R>4 Lane Scaling

Date: 2026-06-26

## Variant ID

`pvw_sab_r_gt4_lane_scaling`

## Delta From Current Promoted Path

Use the existing `sab_pvw_*` active-buffer path with larger independent LUT/SAB
lane counts:

- baseline promoted lane count: `r=4`;
- tested direct larger lane counts: `r=6`, `r=8`;
- backend: `spqlios_avx512`;
- flags: `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`,
  `SAB_PVW_ACTIVE_BUFFER_FUSION=true`;
- no scalar SAB changes;
- no MAT_TRGSW key-format changes.

## Expected Benefit

The candidate would be useful if the shared SAB schedule amortization continued
to dominate dense MAT external-product cost. In that case, larger `r` would
reduce per-lane bootstrapping cost and improve throughput over the current r=4
path.

## Complexity Risk

The MAT external product is dense in the current encrypted selector
representation. Increasing `r` increases body lanes and output updates. The
current AVX512 implementation has small-r specialization, but `r=6` and `r=8`
exercise the generic path rather than a dedicated large-r kernel. This makes
register pressure, cache traffic, and repeated output accumulation the expected
limiting factors.

## Experiment

Stage74 ran one complete-SAB smoke for each larger lane count:

| r | status | speedup vs repeated scalar | evidence |
|---:|---|---:|---|
| 6 | Pass | 1.251x | `repro/stage74_r_scaling_boundary/r6_reps1_runs1/summary.csv` |
| 8 | Pass | 1.199x | `repro/stage74_r_scaling_boundary/r8_reps1_runs1/summary.csv` |

The current r=4 Stage36 10-run reference is mean `1.377x` with CI
`[1.314893, 1.438107]`.

## Decision

`NEGATIVE_NOT_PROMOTED`.

Direct r>4 lane scaling passes correctness and remains faster than repeated
scalar SAB, but it does not beat the r=4 promoted evidence. Do not run the
full repeated/noise/resource campaign for direct r>4 under the current generic
MAT path. Future large-r work needs a new r>4-specific layout or kernel
hypothesis before code changes.

## Required Evidence For Reopening

- a concrete large-r kernel/layout design that reduces dense MAT memory traffic
  or register pressure;
- staged r=6/r=8 MAT external-product correctness;
- complete-SAB repeated A/B versus r=4 and repeated scalar;
- noise/resource gates for promoted r values;
- native counter evidence if the claim depends on load/store/FMA attribution.
