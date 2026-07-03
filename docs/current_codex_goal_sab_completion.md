# Current Codex Goal: PVW/MAT-SAB Completion Route

Date: 2026-06-30

## Current Answer

The project has a complete Stage19+ route for the scoped PVW/MAT-SAB
engineering goal. The local SAB optimization chain is currently closed through
Stage105: scalar/default SAB remains isolated, the explicit `sab_pvw_*` paths
remain gated, current-head smoke gates pass, the scoped complete-SAB
performance/noise/resource evidence is registered, and the former CB5/CB6/CB7
external blockers have been resolved and repackaged into the post-external
final scoped bundle. Stage105 verifies the scoped objective requirement by
requirement.

The route is still scoped, not an unrestricted paper-level novelty claim:

- CB5 is resolved by Stage101 native Linux perf-counter evidence, including
  complete-SAB correctness, retired load/store counters, and AVX512 FP events.
- CB6 is resolved by Stage103 related-work review by scoping the contribution
  to systems/engineering evidence and rejecting broad novelty wording.
- CB7 is resolved by Stage102 reviewed 2025/686 source anchors and explicit
  claim limits.

## Active Goal

Continue from the Stage107 state without changing scalar/default SAB behavior.
The previous scoped systems/engineering package remains complete through
Stage105, but Stage106 opens a new research objective: treat PVW/MAT-SAB as an
r-body MAT-RLWE SAB algorithm and optimize the amortized complete-SAB latency
per processed plaintext lane/bit, `T_total/r`.

Do not reinterpret Stage105 as theoretical optimality. Stage106 fixes the
research loop and primary endpoint while leaving MAT-RLWE SAB optimality open.
Stage107 audits the current MAT kernels and records that they remain dense
row-output `(r+1)^2` implementations, so the next runnable gate is V106-D
layout/locality before any stronger optimality claim. Stage108 has now run
that V106-D gate: the explicit r=6 body-major path is correct but not
performance-positive against both existing r=6 layouts, so it is recorded as a
negative ablation and is not promoted. Stage109 then checks V106-B and records
that body-linear MAT external-product skipping is blocked as a loop-only
change by the current `MAT_TRGSW_DFT` selector/key format. Stage110 then runs
a one-run complete-SAB r=6 tile4/fulltile gate and records fulltile as a
candidate only: 1.026x faster than tile4 in this smoke, with repeated/noise/
resource gates still required.

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
8. Treat Stage105 as the scoped systems/engineering goal-completion audit.
9. Treat Stage106 as the MAT-RLWE SAB research-loop reset:
   primary metric `T_total/r`, existing Stage36 speedups reinterpreted as
   amortized evidence, and theoretical optimality explicitly open.
10. Treat Stage107 as the current source-level MAT kernel structure audit:
    current r=2/r=4/r=6/r=8 kernels are AVX512-specialized but dense
    row-output.
11. Treat Stage108 as the current V106-D result:
    body-major r=6 preserves correctness but is negative/neutral versus the
    existing tile4/fulltile kernels and must not be promoted without new
    complete-SAB `T_total/r` evidence.
12. Treat Stage109 as the current V106-B source gate:
    current selector rows are full PVW encryptions with diagonal gadget
    injection, so body-linear skipping requires a new selector/key-format
    design gate before implementation.
13. Treat Stage110 as routing evidence only:
    r=6 fulltile has a one-run complete-SAB positive signal over tile4, but it
    is not promoted without 3+ repeated runs and noise/resource checks.
14. Preserve the current final-audit status:
   `SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED`.

## Completion Standard

The scoped SAB optimization goal is complete when the scoped engineering
evidence remains passing and every stated claim has matching evidence:
same-backend full-SAB A/B timing, multi-seed correctness/noise, resource/key
overhead, scalar/default isolation, native-perf attribution where claimed,
reviewed 2025/686 source anchors, scoped related-work/novelty review, and a
reproducibility pack with commands, commits, logs, summaries, and decisions.
Claims beyond that scope remain blocked until new evidence is added.

## Stage106 Research Boundary

The new research goal is complete only after a later stage records:

- a formal lower-bound gap model for r-body MAT-RLWE SAB;
- a promoted implementation candidate with deterministic equivalence,
  multi-seed noise, resource, complete-SAB `T_total/r`, and counter evidence;
- an updated literature/novelty review for the exact MAT-RLWE SAB claim;
- a claim ledger that separates amortized algorithmic improvement from
  backend/SIMD implementation effects.
