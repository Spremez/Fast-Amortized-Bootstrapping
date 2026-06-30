# Current Codex Goal: PVW/MAT-SAB Completion Route

Date: 2026-06-30

## Current Answer

The project has a complete Stage19+ route for the scoped PVW/MAT-SAB
engineering goal. The local SAB optimization chain is currently closed through
Stage104: scalar/default SAB remains isolated, the explicit `sab_pvw_*` paths
remain gated, current-head smoke gates pass, the scoped complete-SAB
performance/noise/resource evidence is registered, and the former CB5/CB6/CB7
external blockers have been resolved and repackaged into the post-external
final scoped bundle.

The route is still scoped, not an unrestricted paper-level novelty claim:

- CB5 is resolved by Stage101 native Linux perf-counter evidence, including
  complete-SAB correctness, retired load/store counters, and AVX512 FP events.
- CB6 is resolved by Stage103 related-work review by scoping the contribution
  to systems/engineering evidence and rejecting broad novelty wording.
- CB7 is resolved by Stage102 reviewed 2025/686 source anchors and explicit
  claim limits.

## Active Goal

Continue from the Stage104 state without changing scalar/default SAB behavior.
Maintain the scoped PVW/MAT-SAB engineering package and only upgrade beyond
scoped systems/engineering wording when new theorem, literature, correctness,
noise, resource, parameter, or full-SAB benchmark evidence supports it.

## Execution Route

1. Keep the existing local scoped claim:
   complete-SAB PVW/MAT-SAB throughput improvement is supported only under the
   recorded target parameters, backend, correctness, noise, and resource gates.
2. Keep scalar/default SAB as the immutable comparison baseline unless a future
   explicit stage runs new scalar regression gates.
3. Treat H14-C1 as the preferred explicit local r=6 engineering path, not a
   default path and not a paper-level claim.
4. Use Stage101 counters for attribution, not as a standalone proof of
   theoretical MAT-AVX512 optimality.
5. Use Stage102 source anchors for scoped 2025/686 protocol/citation claims
   and pair PVW/MAT statements with local equivalence/performance evidence.
6. Use Stage103 allowed wording for novelty positioning: scoped
   systems/engineering optimization only.
7. Treat Stage104 as the current final package refresh.
8. Preserve the current final-audit status:
   `SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED`.

## Completion Standard

The scoped SAB optimization goal is complete when the scoped engineering
evidence remains passing and every stated claim has matching evidence:
same-backend full-SAB A/B timing, multi-seed correctness/noise, resource/key
overhead, scalar/default isolation, native-perf attribution where claimed,
reviewed 2025/686 source anchors, scoped related-work/novelty review, and a
reproducibility pack with commands, commits, logs, summaries, and decisions.
Claims beyond that scope remain blocked until new evidence is added.
