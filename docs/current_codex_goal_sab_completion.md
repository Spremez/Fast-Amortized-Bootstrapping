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
resource gates still required. Stage111 runs the required repeated gate and
rejects that candidate: fulltile is 0.974x versus tile4 on repeated complete
SAB PVW mean, despite all correctness gates passing. Stage112 then converts
the body-linear question into a selector/key-format gate and rejects
current-format loop-only off-lane skipping via a concrete shared-mask phase
counterexample. Stage113 then runs the finite r=2 simulator and finds the
lane-local multimask new-format candidate phase-equivalent in toy algebra,
while keeping it blocked on key/ciphertext/noise/resource modeling. Stage114
adds the symbolic resource screen and finds the branch not immediately fatal,
but still blocked from hot-path implementation until a measured toy
representation gate exists. Stage115 runs that measured toy C gate and keeps
the branch alive for a toy arithmetic equivalence prototype only; it still
blocks MOSFHET hot-path integration, noise claims, AVX512 optimality claims,
and complete-SAB speedup claims. Stage116 runs that toy arithmetic gate and
proves dense-vs-lane-local equality for the finite C model while keeping the
current-format drop-offlane path rejected; the next step is a selector/key
skeleton, not SAB integration. Stage117 validates that skeleton as a finite C
term map for r=2/4/6/8 and routes next to real MOSFHET-adjacent type/noise/key
design, still outside the SAB hot path. Stage118 executes that type/noise/key
design gate and routes next to a real-object allocation/phase/noise prototype;
noise remains recorded but unproven. Stage119 then checks the shared-term
semantics and rejects scalar-shared storage for independent LUT lanes; the
active object route is now vector-shared lane-local storage.

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
14. Treat Stage111 as the current r=6 layout decision:
    repeated complete-SAB evidence rejects fulltile promotion; future r=6 work
    needs a new profile-backed hypothesis rather than more fulltile tuning.
15. Treat Stage112 as the current body-linear route decision:
    current shared-mask `MAT_TRGSW_DFT` cannot support loop-only off-lane
    skipping; the next finite path is an r=2 simulator for a new selector/key
    or ciphertext format.
16. Treat Stage113 as the current new-format candidate status:
    lane-local multimask passes r=2 phase simulation, but it changes resource
    semantics and must not be implemented in the hot path until Stage114
    key/ciphertext/noise modeling passes.
17. Treat Stage114 as the current resource screen:
    symbolic accumulator overhead does not immediately kill lane-local
    multimask, but the next valid step is a measured toy representation, not
    complete-SAB integration.
18. Treat Stage115 as the current measured representation gate:
    generated C layout evidence passes for r=2/4/6/8 and N=2048/4096; target
    r=4,N=2048 requested-byte ratio is 1.100 and r=2,N=2048 is 1.333, so the
    only valid next step is toy arithmetic equivalence.
19. Treat Stage116 as the current toy arithmetic gate:
    dense-vs-lane-local mismatches are zero for r=2/4/6 and N=64/256, while
    current-format drop-offlane fails as required; the only valid next step is
    a selector/key skeleton outside the SAB hot path.
20. Treat Stage117 as the current selector skeleton gate:
    `1+2r` term maps pass for r=2/4/6/8 with zero off-lane and missing terms;
    the only valid next step is real type/noise/key design outside SAB.
21. Treat Stage118 as the current real-type design gate:
    r=4,N=2048 has combined accumulator+selector DFT byte ratio 0.866667 and
    key-secret ratio 1.000000, but noise is only recorded-not-proven; next is a
    real-object allocation/phase/noise prototype outside SAB.
22. Treat Stage119 as the current shared-term semantics correction:
    scalar-shared is rejected by negative control; vector-shared has zero phase
    mismatches and zero toy-noise bound violations for r=2/4/6, so Stage120
    must build vector-shared real C structs outside `sab_pvw_*`.
23. Preserve the current final-audit status:
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
