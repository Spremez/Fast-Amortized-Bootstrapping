# Stage102 2025/686 Source-Anchor Review Log

Date: 2026-06-30

## Purpose

Stage102 turns the Stage100 candidate page hints into reviewed source
anchors for the 2025/686 paper. It records page/section-level anchors
and claim limits without storing full paper text.

## Summary

| gate | status | detail |
|---|---|---|
| stage102_fulltext_precondition | PASS | fab686_fulltext=AVAILABLE_UNREVIEWED |
| stage102_candidate_precondition | PASS | stage100_decision=PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED |
| stage102_review_matrix | PASS | reviewed_rows=6 |
| stage102_stage38_update | PASS | Stage38 checklist rows now carry verified source anchors. |
| stage102_decision | PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED | CB7 source-anchor review is complete for scoped 2025/686 citations. |

## Reviewed Anchors

| item | status | anchor | claim limit |
|---|---|---|---|
| FAB_PROTOCOL_STAGES | REVIEWED_SOURCE_ANCHORS_VERIFIED | 2025/686 pp.5-6 Sec.1.2 contributions/MPmul; p.10 Sec.2.2 test vectors/extraction; p.12 Algorithm 1 and Lemma 3.1; p.13 Algorithm 2 bin-SAB; pp.14-15 binary proof and Algorithm 3 tern-SAB; pp.16-17 Algorithm 4 general sparse SAB; p.18 Sec.5/Algorithm 5 packing key switching; pp.20-21 Algorithm 6 functional bootstrapping, Lemma 6.1, Corollary 6.2 | This does not by itself validate PVW/MAT as part of the original paper; PVW/MAT remains the local implementation delta. |
| FAB_COMPLEXITY_MODEL | REVIEWED_SOURCE_ANCHORS_VERIFIED | 2025/686 p.6 states the external-product complexity form for sparse bootstrapping; p.14 gives bin-SAB/MPmul external-product complexity; p.21 gives Algorithm 6 complexity and amortized per-message form in Corollary 6.2 | The local PVW/MAT batching changes throughput constants and lane batching, not the paper's asymptotic SAB theorem. |
| FAB_CORRECTNESS_NOISE | REVIEWED_SOURCE_ANCHORS_VERIFIED | 2025/686 p.12 Lemma 3.1 MPmul noise; p.14 Algorithm 2 correctness/noise proof text; p.21 Lemma 6.1 functional bootstrapping noise and extraction statement; p.33 Appendix B average-case external-product/CMUX noise analysis | Do not cite these anchors as proving the local PVW/MAT path unless local equivalence/noise evidence is cited alongside them. |
| FAB_PARAMETER_SECURITY | REVIEWED_SOURCE_ANCHORS_VERIFIED | 2025/686 p.22 Sec.6.2 parameter/security discussion; p.23 Table 3 repacking/bootstrapping parameters and security-level method; p.24 Table 4 binary/ternary parameters with q=2^64 and rejection-sampling adjustment; pp.27-28 arbitrary sparse-secret comparison | Local experiments currently support binary target and selected added binary parameters; non-binary and all-parameter claims remain separately gated. |
| PVW_SAB_DELTA | REVIEWED_SOURCE_ANCHORS_VERIFIED | Base scalar anchors: 2025/686 pp.5-6 external products/MPmul, p.12 Algorithm 1, p.13 Algorithm 2, p.18 CMUX/packing KS, pp.20-21 Algorithm 6/extract. Local delta: `sab_pvw_*` shared-mask MAT/PVW multi-body batching and explicit-lane PVW/MAT external products in this repository. | This is a local algorithm-engineering delta over the 2025/686 implementation path, not a statement that 2025/686 originally proposed PVW/MAT batching. |
| NOVELTY_BOUNDARY | REVIEWED_SOURCE_ANCHORS_VERIFIED | 2025/686 pp.3,5,7,28 contributions/comparison and pp.29-32 references; Stage103 related-work matrix for post-paper and adjacent work. | Broad novelty for shared-mask batching, SIMD bootstrapping, amortized bootstrapping, or new SAB asymptotics is not supported by this review. |

## Decision

CB7 is resolved for scoped source-anchor use: theorem, algorithm,
complexity, parameter, and protocol citations can be grounded in the
listed paper anchors. Broad novelty and PVW/MAT theorem claims remain
bounded by Stage103 and by local experimental evidence.
