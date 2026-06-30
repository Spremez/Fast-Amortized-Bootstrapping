# Stage103 Related-Work And Novelty Review Log

Date: 2026-06-30

## Purpose

Stage103 resolves CB6 by converting related-work risk into an explicit
claim boundary. It uses only real, named sources and records which
contribution wordings are supported or blocked.

## Summary

| gate | status | detail |
|---|---|---|
| stage103_stage102_precondition | PASS | stage102_decision=PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED |
| stage103_source_verification | PASS | verified_sources=11/11 |
| stage103_related_work_matrix | PASS | axes=5 |
| stage103_novelty_boundary | PASS_SCOPED_BOUNDARY | scoped_or_supported=3; broad_rejections=2 |
| stage103_decision | PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED | CB6 resolved by scoped contribution boundary; broad novelty claims remain blocked. |

## Novelty Decisions

| claim | decision | allowed wording | blocked wording |
|---|---|---|---|
| S103-N1 | SUPPORTED_SCOPED_ENGINEERING_CLAIM | A scoped systems/engineering optimization with measured complete-SAB throughput gains under explicit flags. | Do not state universal, all-parameter, or default-path acceleration. |
| S103-N2 | REJECT_BROAD_NOVELTY_PRIOR_ART | The local system explores PVW/MAT shared-mask multi-body batching inside the 2025/686 SAB implementation. | Do not claim general first shared-mask batching or first batched TFHE bootstrapping. |
| S103-N3 | REJECT_NOT_SUPPORTED | Constant-factor throughput optimization for the implemented schedule. | Do not claim a new asymptotic SAB algorithm without a new proof. |
| S103-N4 | SUPPORTED_COUNTER_EVIDENCE_NOT_OPTIMALITY | Hardware-counter attribution is available on native Linux for analysis. | Do not claim theoretical optimality solely from one perf run. |
| S103-N5 | ALLOW_SCOPED_NOVELTY_CANDIDATE_WITH_RELATED_WORK_CAVEAT | A scoped implementation contribution and empirical study of PVW/MAT external-product batching for 2025/686 SAB. | Do not call it novel without acknowledging batch/SIMD/common-mask bootstrapping prior art. |

## Decision

CB6 is resolved by scoping, not by broad novelty promotion. The evidence
supports a systems/engineering contribution: a measured PVW/MAT
multi-body external-product batching path for the 2025/686 SAB
implementation. It does not support claims of first shared-mask
bootstrapping, general batch bootstrapping novelty, new SAB asymptotics,
or all-parameter/non-binary coverage.
