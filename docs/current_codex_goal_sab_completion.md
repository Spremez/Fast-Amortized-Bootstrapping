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
active object route is now vector-shared lane-local storage. Stage120 then
builds standalone vector-shared C structs with polynomial arrays and
negacyclic phase/noise checks. This advances the route to DFT/conversion
prototype readiness, still outside MOSFHET torus/FFT external products and
outside SAB hot paths. Stage121 then proves exact DFT/conversion semantics in
a modular prototype, Stage122 proves structured external-product arithmetic
against a dense clean reference, and Stage123 moves that structured EP smoke
through the actual MOSFHET torus/SPQLIOS DFT API. Stage123 passes with zero
coefficient mismatches and zero DFT/noisy DFT mismatches under a fixed 1024
torus-unit tolerance, with maximum observed DFT gap 619. This opens only a
MOSFHET-adjacent vector-shared type/API sketch. Stage124 then compile-checks
that skeleton against MOSFHET allocation and production DFT conversion:
component ownership, metadata, lane coverage, and DFT roundtrip all pass for
k=1, T=7, r=2/4/6, and N=1024/2048. This is still not complete-SAB
`T_total/r`, AVX512 optimality, gadget decomposition, selector encryption, or
SAB hot-path integration evidence. Stage125 then checks compact selector
gadget decomposition and diagonal injection using production DFT. It passes
with zero coefficient-vs-DFT mismatches under a fixed 16384 torus-unit
tolerance and rejects body-only selector rows. The result opens compact
selector encryption/noise modeling only; r=2 is count break-even once
decomposition streams are included, while r=4/r=6 remain count-positive.
Stage126 then verifies deterministic compact selector encryption/noise
semantics: coefficient phase, production DFT phase, exact modeled noise, and
conservative noise bound gates all pass, while body-only encrypted selector
rows remain rejected. This opens only isolated compact external-product kernel
work outside `sab_pvw_*`. Stage127 then factors that external product into a
generated reusable `compact_ep_kernel_dft` with explicit scratch. Component,
phase, and noise-model mismatch counts are zero, body-only kernel rows remain
rejected, and the count model remains positive for r=4/r=6 while r=2 is
break-even once decomposition terms are included.

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
23. Treat Stage120 as the current real-struct phase/noise gate:
    vector-shared polynomial structs pass 30 phase/noise rows for r=2/4/6,
    N=32/64, seeds 0..4, with zero mismatches and zero noise-bound violations;
    the next valid step is DFT/conversion prototyping outside SAB.
24. Treat Stage121 as the current vector-shared DFT/conversion gate:
    exact modular DFT conversion passes 30 rows for r=2/4/6, N=32/64,
    seeds 0..4. Roots, round-trip conversion, clean phase, noisy phase, and
    noise bounds all pass. The next valid step is structured vector-shared
    external-product arithmetic prototyping outside `sab_pvw_*`.
25. Treat Stage122 as the current structured EP arithmetic gate:
    structured vector-shared EP passes 30 rows for r=2/4/6, N=32/64,
    seeds 0..4. Dense clean phase equals structured phase, coefficient EP
    equals exact DFT EP, noisy bounds pass, and body-only off-lane skipping
    fails as a negative control. The next valid step is production torus/FFT
    smoke outside `sab_pvw_*`.
26. Treat Stage123 as the current production FFT smoke gate:
    MOSFHET `FFT_LIB=spqlios` static build, standalone probe compile/run,
    coefficient structured EP, production DFT structured EP, noisy DFT
    structured EP, negative control, and term-ratio layout gates all pass.
    The next valid step is MOSFHET-adjacent vector-shared type/API sketching
    outside `sab_pvw_*`, not hot-path integration or a speedup claim.
27. Treat Stage124 as the current MOSFHET type/API skeleton gate:
    the vector-shared accumulator and compact selector DFT skeleton compile and
    run against MOSFHET, all ownership/metadata/coverage/roundtrip checks pass,
    and r=4 records selector count 112 versus current dense 175 plus total
    count 120 versus 180. The next valid step is compact selector gadget
    decomposition and diagonal injection outside `sab_pvw_*`.
28. Treat Stage125 as the current compact selector gadget gate:
    production DFT compact gadget rows pass for k=1, T=7, Bg_bit=7, r=2/4/6,
    and N=1024/2048. Coefficient-vs-DFT mismatches are zero under 16384
    torus-unit tolerance, body-only selector rows are rejected, and layout
    count evidence shows r=2 break-even but r=4/r=6 positive. The next valid
    step is compact selector encryption/noise modeling outside `sab_pvw_*`.
29. Treat Stage126 as the current compact selector encryption/noise gate:
    deterministic encrypted selector rows pass coefficient phase, production
    DFT, modeled-noise, noise-bound, and negative-control gates for r=2/4/6.
    The maximum DFT gap is 14449 under tolerance 131072, and the maximum
    modeled noise is 13022 under bound 917504. The next valid step is an
    isolated compact external-product kernel outside `sab_pvw_*`.
30. Treat Stage127 as the current isolated compact EP kernel gate:
    `compact_ep_kernel_dft` passes component, phase, noise-model, negative
    control, and complexity gates for r=2/4/6. Max component/phase gaps are
    14645/14653 under tolerance 131072. The next valid step is a
    MOSFHET-adjacent compact EP API boundary outside `sab_pvw_*`.
31. Treat Stage128 as the current compact EP API boundary gate:
    MOSFHET-adjacent selector/output/scratch API shapes pass ownership,
    metadata, invalid-guard, no-hot-allocation, component, phase, noise-model,
    negative-control, and complexity gates for r=2/4/6. Max component/phase
    gaps are 14605/14608 under tolerance 131072. The next valid step is
    isolated compact EP microbench/profiling outside `sab_pvw_*`.
32. Treat Stage129 as the current isolated compact EP microbench gate:
    build, compile, run, API correctness replay, and benchmark rows pass, but
    the promotion signal is neutral. r=4 full speedup is 0.925687 at N=512 and
    0.888032 at N=1024; r=6 is positive at 1.063672 and 1.109918. Compact
    addmul is positive for r=4/r=6, but compact decomposition/DFT is slower.
    The next valid step is a decompose/DFT reuse or streaming gate, not SAB
    integration.
33. Treat Stage130 as the current shared-source compact EP gate:
    one shared source/mask plus r body polynomials passes component, phase,
    noise-model, negative-control, and isolated microbench gates outside
    `sab_pvw_*`. Full speedups are 1.281272/1.153336 for r=4 at N=512/1024 and
    1.478479/1.369582 for r=6 at N=512/1024; r=2 remains near break-even or
    negative. The next valid step is production API/header design for this
    shared-source EP shape, not SAB integration.
34. Treat Stage131 as the current shared-source production API gate:
    MOSFHET public types and functions for shared-source compact EP build,
    link, and pass component/phase/noise/negative-control checks for r=2/4/6
    and N=512/1024. The output type is lane-pair
    `MAT_TRGSW_COMPACT_OUTPUT_DFT`, not a true shared-output-mask
    `PVW_TMLWE_DFT`. The next valid step is isolated SAB CMUX/RGSW integration
    design around this output type.
35. Preserve the current final-audit status:
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

36. Treat Stage132 as the current lane-pair CMUX consumption gate:
    `PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED`. The compact shared-source EP output can be consumed by
    per-lane `base + delta` CMUX updates for r=2/4/6 and N=512/1024 with zero
    component, phase, consumer, and noise-model mismatches. A single
    shared-output-mask collapse fails as required. The next valid step is a
    compact lane-state accumulator design for RGSW monomial and sparse
    schedule integration, not complete `T_bootstrap/r` claims.

37. Treat Stage133 as the current lane-state closure audit:
    `PASS_STAGE133_CLOSURE_AUDIT_DIRECT_SHARED_SOURCE_ITERATION_BLOCKED`. Lane-pair compact output is valid as internal accumulator
    state, but direct iteration of the Stage131 shared-source compact EP is
    blocked because the next source would have per-lane masks rather than one
    shared mask. The next valid implementation stage is generalized lane-pair
    input compact EP, followed only later by RGSW/sparse schedule integration.

38. Treat Stage134 as the current generalized lane-pair input EP gate:
    `NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED`. It validates the closure-capable input shape selected by
    Stage133 and records full-kernel timing with min r=4/r=6 speedup
    0.910791. If this remains neutral, the next valid step is lane-pair
    decompose/DFT reuse or streaming, not RGSW/sparse integration.

39. Treat Stage135 as the current decompose/DFT reuse target gate:
    `PASS_STAGE135_DECOMP_DFT_REUSE_TARGETS_READY_STAGE136`. The r=4 generalized lane-pair input path needs up to
    1.152711 decompose/DFT speedup to break even and
    1.245156 for a 5pct full-kernel gain. RGSW/sparse integration
    remains rejected until Stage136 improves this measured blocker.

40. Treat Stage136 as the current batched decompose/DFT gate:
    `FAIL_STAGE136_BATCHED_DECOMP_DFT_GATE`. It checks exact equivalence against `polynomial_decompose_i`
    and benchmarks current versus batched decompose/DFT. Minimum r=4 speedup is
    ; full SAB claims remain blocked.
