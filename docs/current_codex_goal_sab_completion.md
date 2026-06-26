# Current Codex Goal: PVW/MAT-SAB Completion Route

Date: 2026-06-26

## Current Answer

The project already has a complete Stage19+ route for the scoped
PVW/MAT-SAB engineering goal. The local SAB optimization chain is currently
closed through Stage100: scalar/default SAB remains isolated, the explicit
`sab_pvw_*` paths remain gated, current-head smoke gates pass, the scoped
complete-SAB performance/noise/resource evidence is registered, and the
registered 2025/686 full-text artifact now has candidate source-anchor pages
for manual review.

The route is not a paper-level completion yet. Three stronger-claim blockers
remain:

- CB5: native Linux/perf hardware-counter evidence for MAT-AVX512
  load/store/FMA attribution.
- CB6: manual novelty and related-work claim-to-source review.
- CB7: 2025/686 full text is now registered as a local hashed artifact, but
  theorem-level protocol and citation claims still require source-anchor
  review.

## Active Goal

Continue from the Stage98 state without changing scalar/default SAB behavior.
Maintain the current scoped PVW/MAT-SAB engineering package, reprobe external
unlock conditions when useful, and only upgrade final claims when the relevant
native-perf, full-text, novelty, correctness, noise, resource, and full-SAB
benchmark gates are satisfied.

## Execution Route

1. Keep the existing local scoped claim:
   complete-SAB PVW/MAT-SAB throughput improvement is supported only under the
   recorded target parameters, backend, correctness, noise, and resource gates.
2. Keep scalar/default SAB as the immutable comparison baseline unless a future
   explicit stage runs new scalar regression gates.
3. Treat H14-C1 as the preferred explicit local r=6 engineering path, not a
   default path and not a paper-level claim.
4. Use Stage99 to reprobe the post-Stage98 external blocker state.
5. Use Stage100 candidate anchors only as a manual-review accelerator; they
   are not verified source anchors and do not upgrade theorem-level or novelty
   claims.
6. If native perf becomes available, rerun Stage28 with
   `STAGE28_RUN_BENCH=1` and perform manual counter interpretation before
   claiming MAT-AVX512 theoretical memory-traffic superiority.
7. Use the registered 2025/686 artifact from Stage38 only after filling the
   Stage38 review checklist with concrete source anchors for protocol,
   complexity, correctness/noise, parameter/security, PVW-SAB delta, and
   novelty-boundary rows.
8. If both source review and related-work review are completed, refresh the
   final package and claim boundary. Until then, keep the final status scoped:
   `SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED`.

## Completion Standard

The SAB optimization goal is fully complete only when the scoped engineering
evidence remains passing and all desired final claims have matching evidence:
same-backend full-SAB A/B timing, multi-seed correctness/noise, resource/key
overhead, scalar/default isolation, native-perf attribution where claimed,
reviewed 2025/686 source anchors, related-work/novelty review, and a
reproducibility pack with commands, commits, logs, summaries, and decisions.
