# Stage 10 Engineering Report

Date: 2026-06-12

## Objective

Collect the current evidence for the `sab_pvw_*` optimization path into a
claim-to-evidence report. This report is scoped to an engineering result for
the 2025/686 binary `SET_2_3_2048` target shape on the WSL/Linux `spqlios`
performance platform.

Machine-readable artifacts:

- `repro/stage10_claim_evidence_matrix.csv`
- `repro/stage_commit_registry.csv`

## Supported Engineering Claim

Within the current binary target scope, the new `sab_pvw_*` path preserves the
scalar SAB route and improves complete full-output SAB throughput over repeated
scalar SAB for multiple independent LUT/SAB lanes.

Primary same-backend full SAB throughput evidence:

| variant | backend | r | runs | reps/run | PVW mean us | scalar repeated mean us | speedup |
|---|---|---:|---:|---:|---:|---:|---:|
| clear-elision | spqlios | 2 | 3 | 2 | 18,684,294.000 | 23,642,989.000 | 1.269x |
| clear-elision | spqlios | 4 | 3 | 2 | 35,044,592.833 | 46,848,311.333 | 1.337x |

The same-backend rows are the primary algorithmic throughput evidence.
Backend/SIMD rows are recorded separately and are not counted as algorithmic
gain.

## Correctness And Noise

Final-output clear-elision deterministic sweeps:

| r | seeds | points | PVW failures | scalar failures | pair failures | gap range | avg gap |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 50 | 204,800 | 0 | 0 | 0 | -0.470 to 0.636 | -0.0039 |
| 4 | 50 | 409,600 | 0 | 0 | 0 | -0.541 to 0.636 | -0.0313 |

Stage-level smoke probes passed for `r=2` and `r=4` with zero pair failures at
the measured boundaries:

- blind-rotation coefficient 0;
- extract;
- TLWE materialization;
- packing KS;
- HW-KS.

The stage probe shows that PVW-vs-scalar pair delta is small through packing
KS and becomes visibly larger after HW-KS. It remains a `trials=1` smoke and
does not replace the final-output 50-seed sweeps.

## Resource Cost

Recorded resource evidence:

| r | PVW key bytes / scalar repeated | PVW max RSS KB | scalar max RSS KB | PVW keygen / scalar keygen |
|---:|---:|---:|---:|---:|
| 2 | 1.013617x | 382,740 | 387,268 | 1.236x |
| 4 | 1.065349x | 769,208 | 771,208 | 1.179x |

The public bootstrap key estimate and process RSS are acceptable for the
current engineering claim. Keygen overhead is measurable and must be reported
with the speedup.

## Claim Boundaries

Supported:

- `sab_pvw_*` is an additive path; scalar SAB remains runnable.
- Full-output SAB throughput improves over repeated scalar SAB for `r=2` and
  `r=4` on WSL/Linux `spqlios`.
- Algorithmic speedup is separated from backend/SIMD effects.
- Final-output correctness/noise gates pass for deterministic 50-seed
  campaigns at `r=2` and `r=4`.
- Reproducibility artifacts exist for commands, logs, summaries, and commit
  milestones.

Not supported yet:

- paper-grade novelty claim;
- paper-grade failure-rate bound;
- universal claim beyond the binary `SET_2_3_2048` target scope;
- ternary/include-zero/gaussian SAB branches;
- strict paired variant A/B between pre-variant and clear-elision commits.

## Next Decision

The engineering report is now strong enough to state a scoped systems
optimization claim. Upgrading to a paper claim requires a deeper related-work
audit, a declared failure-rate target, independent-trial statistics, and a
larger benchmark matrix.
