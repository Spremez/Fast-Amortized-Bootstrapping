# Stage 39 Optional Variant Triage Log

Date: 2026-06-26

## Purpose

Stage 39 decides whether to start new algorithmic variant work beyond the promoted active-buffer MAT-SAB path. It preserves prior neutral and blocked evidence instead of repeatedly modifying hot paths without a new gate.

## Candidate Matrix

| candidate | decision | current evidence | next gate |
|---|---|---|---|
| S39-NONBINARY-PVW-SAB | BLOCKED_REQUIRES_PROTOCOL_DESIGN_AND_FULLTEXT | branch_summary pvw_target=EXPECTED_UNSUPPORTED; Stage38=BLOCKED_FULLTEXT_MISSING | Provide full 2025/686 text, write non-binary PVW-SAB design, then start with staged r=1/2 correctness before performance work. |
| S39-DEEPER-SCHEDULE-FUSION | DEFER_PRIOR_NEUTRAL | Stage23 r=4 schedule-fused mean speedup 1.335x; recorded neutral | Only reopen if a new profile shows a larger schedule/copy/materialization cost than the Stage 23/24 evidence. |
| S39-MAT-R4-LAYOUT | BLOCKED_NATIVE_COUNTERS_OR_ISOLATED_LAYOUT_EXPERIMENT | final audit A8=BLOCKED_EXTERNAL; Stage37=BLOCKED_EXTERNAL_PERF | Run Stage37 on native/perf-enabled Linux, or implement a reversible isolated key-layout experiment with no default key-format change. |
| S39-DIRECT-POSTPROC | DEFER_TAIL_SMALL | Stage24 max post-processing tail 1.261195% below 2.0% threshold | Reopen only if a new body optimization raises tail cost above the threshold. |
| S39-AVX512-RSPECIFIC | BLOCKED_NATIVE_COUNTERS | Stage37=BLOCKED_EXTERNAL_PERF; final audit A8=BLOCKED_EXTERNAL | Collect native perf counters and compare against Stage22 specialized/generic data. |
| S39-OVERALL | NO_NEW_VARIANT_PROMOTED_CURRENTLY | final audit A9=SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED | Proceed to Stage40 freeze for current scoped claim, or select one blocked/optional candidate explicitly after supplying its prerequisite evidence. |

## Decision

The promoted active-buffer MAT-SAB path already has scoped engineering evidence; remaining stronger claims are external or optional rather than an immediate new-code requirement.
