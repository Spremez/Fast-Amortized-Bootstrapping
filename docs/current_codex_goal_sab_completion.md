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

41. Treat Stage137 as the current decompose/DFT attribution gate:
    `PASS_STAGE137_DFT_CONVERSION_DOMINANT_READY_DFT_ROUTE`. It measures current full decompose/DFT, decompose-only, and
    DFT-only timing. For r=4, minimum DFT fraction is 0.862257; full SAB
    claims remain blocked.

42. Treat Stage138 as the shared-mask compact MAT gate:
    `PASS_STAGE138_SHARED_MASK_COMPACT_PROMOTED_READY_SAB_INTEGRATION`. It compares repeated lane-pair EP against production compact
    shared-mask EP using `T_kernel/r`. For r=4, per-bit speedup is
    1.293981-1.491182; complete SAB claims remain blocked.

43. Treat Stage139 as the compact closure audit:
    `PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE`. Minimum mask mismatch count is 512.000000. Direct diagonal
    compact output is not a valid PVW_TMLWE SAB accumulator; Stage140 must
    target full MAT/shared-output compact closure.

44. Treat Stage140 as the closed full-MAT attribution gate:
    `PASS_STAGE140_CLOSED_FULLMAT_DFT_COUNT_LOWER_BOUND_READY_STAGE141`. Production closed full-MAT uses `(r+1)T` input DFT conversions,
    which is the Torus-input lower bound for a one-mask/r-body state. Stage141
    must target either lazy state or addmul/AVX, then validate at CMUX/SAB level.

45. Treat Stage141 as the AVX512 closed full-MAT target gate:
    `FAIL_STAGE141_AVX512_CLOSED_FULLMAT_GATE`. r4-unrolled versus generic speedup is 1.093355-1.373156
    for r=4,T=1,N=1024/2048, but specialized-kernel correctness is blocked.
    No full SAB rerun may use these flags until Stage142 fixes or rejects the
    AVX512 small-r/r4-unrolled correctness issue.
46. Treat Stage142 as the AVX512 FMA-order correctness repair:
    `PASS_STAGE142_AVX512_FMA_ORDER_FIX_PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN`. The r4-unrolled closed full-MAT mean kernel speedup is
    1.176373-1.267909. Next required gate: complete SAB A/B using amortized
    `T_bootstrap/r`, not raw kernel time.
47. Treat Stage143 as the first complete SAB smoke after the AVX512 FMA-order
    fix: `SMOKE_STAGE143_FULL_SAB_R4_UNROLLED_POSITIVE_REPEATED_REQUIRED`. Primary metric is `T_bootstrap/r`. r4-unrolled active
    PVW lane time is 7125020.500 us versus generic active
    7586131.750 us; repeated Stage144 is still required.
48. Treat Stage144 as the repeated complete-SAB gate for the r=4 r4-unrolled
    candidate: `WEAK_STAGE144_R4_UNROLLED_POSITIVE_STATS_REVIEW_REQUIRED`. Primary endpoint `T_bootstrap/r` gives mean paired
    r4/generic speedup 1.000249 with CI95
    [0.835834, 1.164664].
    Noise/resource are recorded in the Stage144 repro pack.
49. Treat Stage145 as the r4-unrolled promotion-policy audit:
    `WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE`. The explicit r4-unrolled path is retained only for
    ablation/variance analysis; it is not promoted to default or final claim.
50. Treat Stage146 as the r4-unrolled variance-attribution gate:
    `PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT`. This stage may guide the next research route, but it does not
    promote the r4-unrolled path or modify scalar/default SAB behavior.
51. Treat Stage147 as the H14 r=6 current-head route gate:
    `PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT`. This stage confirms or rejects the next branch after
    r4-unrolled remains explicit-only; it is not a final speedup claim.
52. Treat Stage148 as the H14 r=6 repeated refresh gate:
    `PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE`. This stage records current-head repeated/noise/resource
    evidence for the explicit backend route; it is still not a default-path or
    paper-level novelty claim by itself.
53. Treat Stage149 as the H14 r=6 claim-policy gate:
    `PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT`. It permits only scoped explicit-path engineering wording and
    keeps default-path/paper-novelty claims blocked.
54. Treat Stage150 as the final-package refresh gate:
    `PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED`. It fixes the comparison dimension to
    `T_complete_bootstrap(r)/r` and records the current scoped H14 r=6
    explicit-path result. The next valid stage must pick a concrete
    implementation candidate and verify it against the same amortized endpoint.
55. Treat Stage151 as the H14 r=6 fulltile backend smoke gate:
    `WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL`. It is a concrete implementation-candidate gate, not a final
    claim. If it is not positive, fulltile remains an ablation and the next
    stage must choose a different hot-path candidate.
56. Treat Stage152 as the isolated dual-sub kernel gate:
    `PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE`. It is necessary evidence for H14-C3 but cannot be used as a
    complete SAB speedup claim. Full integration requires a later `T_bootstrap/r`
    gate if this local result is strong enough.
57. Treat Stage153 as the dual-sub full-SAB gate:
    `NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED`. The explicit flag path preserves scalar/default SAB and
    confirms the pairable fraction `(h+1)*(2^r_prec-1)`, but this fraction is
    too small for a strong full-SAB claim unless a broader pairing schedule is
    found.
58. Treat Stage154 as the bodymajor full-SAB closeout:
    `REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER`. It closes the Stage108 missing complete-SAB evidence for
    `MAT_TRGSW_AVX512_R6_BODYMAJOR` under the H14 r=6 backend path.
59. Treat Stage155 as the same-format frontier refresh:
    `PASS_STAGE155_SAME_FORMAT_FRONTIER_ROUTE_TO_REPRESENTATION_GATE`. The current same-format r-body path keeps the scoped H14 r=6
    evidence, rejects blind bodymajor/fulltile/dual-sub continuation, and
    selects a representation-changing feasibility gate as the next valid step.
60. Treat Stage156 as the lazy-DFT closure gate:
    `REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED`. It rejects the naive DFT-only accumulator route and routes
    next to exact decomposed-cache or compact/shared-source feasibility, not to
    direct `sab_pvw_*` integration.
61. Treat Stage157 as the sub-decompose fusion preflight:
    `PASS_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_POSITIVE_IMPLEMENTATION_CANDIDATE`. It gives or denies permission to implement direct
    `decompose(in2-in1)` behind an explicit PVW/MAT-SAB flag.
62. Treat Stage158 as the sub-decompose fusion full-SAB gate:
    `SMOKE_STAGE158_SUB_DECOMP_FUSION_FULLSAB_POSITIVE_REPEATED_REQUIRED`. It is the first complete-SAB check for the Stage157
    implementation candidate; promotion still requires repeated gates.
63. Treat Stage159 as the sub-decompose fusion repeated gate:
    `PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE`. This stage decides whether the Stage158 candidate is a
    promotion candidate, weak/neutral ablation, or failed path under strict
    complete-SAB research gates.
64. Treat Stage160 as the post-fusion frontier gate:
    `PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED`. It prevents a theory loop by selecting the next target from
    measured post-fusion component shares rather than speculative layout work.
65. Treat Stage161 as the post-fusion attribution gate:
    `PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED`. It prevents overclaiming by separating objdump/time proxy
    evidence from native hardware-counter proof.
66. Treat Stage162 as the materialization-count feasibility gate:
    `PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED`. It prevents conflating backend IFFT batching with algorithmic
    materialization-count reduction.
67. Treat Stage163 as the from_DFT backend batching microbench:
    `NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED`. This stage decides whether component-major batching of
    `polynomial_DFT_to_torus_add` deserves a later complete-SAB gate. It must
    not be used as an algorithmic count-reduction or final bootstrapping claim.
68. Treat Stage164 as the representation closure route:
    `PASS_STAGE164_REPRESENTATION_ROUTE_TO_CLOSED_FULL_MAT_STREAMING_GATE`. It does not claim a new SAB algorithm; it selects Stage165 as
    the next exact-output microbench and keeps structured compact keygen behind
    proof gates.
69. Treat Stage165 as the closed full-MAT streaming microbench:
    `REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX`. It decides whether row-streamed decompose/DFT/addmul should
    be integrated; if not positive, keep the current tiled AVX path.
70. Treat Stage166 as the shared-output compact algebra gate:
    `PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED`. Generic compact shared-output is not a drop-in optimization;
    it needs structured keygen/security/noise proof before SAB integration.
71. Treat Stage167 as the CB5 native r=6 counter refresh:
    `PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED`. Use it to interpret the current exact path's hardware
    behavior; do not treat counters alone as theoretical optimality proof.
72. Treat Stage168 as the native counter frontier:
    `PASS_STAGE168_ROUTE_TO_NATIVE_REPEATED_AND_SPLIT_COUNTERS`. Use Stage167 counters only for attribution; final native
    throughput and component-level claims require Stage169/170.
73. Treat Stage169 as the CB5 native repeated r=6 gate:
    `PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE`. It provides native no-perf repeated complete-SAB throughput
    evidence for the current exact path, but not theoretical optimality.
74. Treat Stage170 as split component counter attribution:
    `PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED`. It separates MAT EP/subdecomp from from_DFT materialization
    using native CB5 counters, while keeping Stage169 as the complete-SAB
    throughput endpoint.
75. Treat Stage171 as structured compact proof-route gate:
    `PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY`. It provides a bounded algebraic and Stage170-informed
    projection, not an implementation or final speedup claim.
76. Treat Stage172 as the current claim boundary:
    `PASS_STAGE172_FRONTIER_CLOSEOUT_RECORDED`. The next automatic engineering route is Stage174
    from_DFT locality; Stage173 is proof work only if explicitly prioritized.
77. Treat Stage174 as bounded from_DFT backend gate:
    `NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED`. It does not change
    MAT/SAB algorithmic claims because the microbench promotion gate did not
    pass.
78. Treat Stage175 as the post-direct-scale route refresh:
    `PASS_STAGE175_ROUTE_TO_STRUCTURED_COMPACT_TOY_GATE`. Complete-SAB claims remain unchanged; next bounded work is
    Stage173 structured compact finite phase/noise toy.
79. Treat Stage173 as finite phase/noise toy evidence:
    `PASS_STAGE173_PHASE_NOISE_TOY_PROOF_STILL_OPEN`. It improves the proof-route evidence for structured compact
    MAT-SAB while keeping security/API/full-SAB claims blocked.
80. Treat Stage176 as the compact security/API boundary:
    `BLOCK_STAGE176_STRUCTURED_COMPACT_SECURITY_API_NOT_CLOSED_REDIRECT_FULL_MAT`. Stage173 phase/noise toy evidence does not overcome missing
    standard security distribution and shared-mask API closure. Do not implement
    compact SAB directly; continue exact full-MAT `T_bootstrap/r` work.
81. Treat Stage177 as the verified literature boundary:
    `PASS_STAGE177_VERIFIED_LITERATURE_BOUNDARY_NO_STRONG_NOVELTY_CLAIM`. Real adjacent work includes 2025/696 and prior amortized,
    batch, PVW packing, FHEW/TFHE sources. Strong novelty claims remain
    blocked; proceed to exact full-MAT `T_bootstrap/r` frontier work.
82. Treat Stage178 as the per-bit exact full-MAT frontier:
    `PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT`. The current complete-SAB r=6 endpoint is
    1.131666667x mean speedup on
    `T_bootstrap/r` versus repeated scalar. Stage179 may audit MAT
    EP/subdecomp only if it stays tied to complete-SAB impact.
83. Treat Stage179 as the MAT EP microarchitecture audit:
    `PASS_STAGE179_AUDIT_SELECT_MAT_EP_SPLIT_PROBE_NO_CODE`. Current r=6 MAT-aware AVX512 exists. Stage180 must split
    sub_decompose, torus_to_DFT, and tiled addmul before any new exact-path
    implementation branch opens.
84. Treat Stage180 as the MAT EP split probe:
    `PASS_STAGE180_SPLIT_PROBE_RECORDED`. It measures sub-decompose,
    torus-to-DFT rows, addmul, and combined-current timing for the
    exact r=6 MAT EP block. Code promotion still requires projected
    complete-SAB `T_bootstrap/r` impact.
85. Treat Stage181 as the AVX512 sub-decompose gate:
    `REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER`. The new
    implementation is default-off and recorded as a negative ablation;
    no full-SAB acceleration claim is allowed from it.
86. Treat Stage182 as the exact-path negative frontier:
    `PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED`. Stage181 rejects sub-decompose AVX512. Future exact-path
    code requires a new dataflow mechanism with projected complete-SAB impact;
    compact SAB remains proof/literature gated.
87. Treat Stage183 as the addmul dataflow screen:
    `PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION`. The code already contains MAT-aware AVX512 tiled,
    fulltile, and bodymajor addmul variants. Prior gates reject those dataflow
    families, so no new exact addmul code is allowed without a new mechanism.
88. Treat Stage184 as the exact-route claim closeout:
    `PASS_STAGE184_EXACT_ROUTE_CLOSEOUT_CLAIM_REFRESH`. Scoped complete-SAB `T_bootstrap/r` speedup wording is
    allowed; AVX512 theoretical optimality, sub-decompose speedup, and
    implemented compact MAT-SAB claims are denied.
89. Treat Stage185 as the research/repro package refresh:
    `PASS_STAGE185_RESEARCH_REPRO_PACKAGE_REFRESH`. It packages the current evidence around the original
    MAT-RLWE/r-body SAB research objective and confirms that the overall goal
    remains active: scoped complete-SAB speedup is supported, but theoretical
    optimality and compact/shared-output implementation remain open.
90. Treat Stage186 as the compact proof unlock audit:
    `BLOCK_STAGE186_COMPACT_PROOF_UNLOCK_NOT_READY`. Compact/shared-output MAT-SAB is not unlocked for
    implementation. Stage138 remains kernel-level motivation only; Stage139,
    Stage176, and Stage177 continue to block full SAB code and strong claims.
91. Treat Stage187 as the compact proof obligation draft:
    `PASS_STAGE187_COMPACT_PROOF_DRAFT_IMPLEMENTATION_STILL_DENIED`. Compact/shared-output MAT-SAB now has explicit theorem
    obligations and falsification gates. Only isolated proof probes are allowed;
    production SAB code remains denied.
92. Treat Stage188 as the scoped manuscript skeleton:
    `PASS_STAGE188_SCOPED_MANUSCRIPT_SKELETON_READY`. It is a writing artifact constrained by Stage185/187 claim
    guards, not a final paper or proof. Final citation verification remains
    required before submission-level claims.
93. Treat Stage189 as the closed-state linear probe:
    `PASS_STAGE189_T2_PUBLIC_CLOSURE_PROBE_DIRECT_SHARED_MASK_REJECTED`. Direct public projection from lane-local compact masks to
    one shared PVW_TMLWE mask is rejected for r>1. Compact/shared-output SAB
    implementation remains denied; only isolated T1/T4 proof probes or a new
    measured dataflow mechanism may proceed.
94. Treat Stage190 as the selector distribution distinguisher:
    `PASS_STAGE190_T1_SELECTOR_DISTRIBUTION_DISTINGUISHERS_RECORDED_IMPLEMENTATION_STILL_DENIED`. Compact selector row deletion, deterministic zero rows, and
    forced equal/shared masks are public distribution changes. T1 remains
    unproven; production compact SAB implementation remains denied.
95. Treat Stage191 as the secret-correction noise/resource gate:
    `PASS_STAGE191_T4_SECRET_CORRECTION_LOWER_BOUND_RECORDED_IMPLEMENTATION_DENIED`. Secret-correction or key-switch closure remains proof-only:
    it needs explicit key-format, latency, resource, and noise recurrence
    evidence before any `sab_pvw_*` production implementation.
96. Treat Stage192 as compact admission and route selection:
    `PASS_STAGE192_COMPACT_IMPLEMENTATION_DENIED_ROUTE_EXACT_ADDMUL_PREFLIGHT`. Compact/shared-output SAB implementation is denied after
    T1/T2/T4 gates. The next non-theory executable route is Stage193 exact
    full-MAT addmul dataflow preflight.
97. Treat Stage193 as exact addmul dataflow preflight:
    `PASS_STAGE193_EXACT_ADDMUL_PREFLIGHT_NO_CODE_ROUTE_DFT_MECHANISM`. Addmul code remains denied: the only new local dec-cache
    mechanism has an optimistic r=6 bound below the 3% complete-SAB gate, and
    prior fulltile/bodymajor/streaming families remain rejected. Next route:
    Stage194 DFT/conversion mechanism preflight.
98. Treat Stage194 as exact DFT/conversion preflight:
    `PASS_STAGE194_EXACT_DFT_PREFLIGHT_NO_CODE_ROUTE_SCOPED_REFRESH`. DFT/conversion code remains denied: same-format count
    reduction is closed, backend batching/direct-scale candidates were neutral,
    and representation routes need closure/noise proof. Next route: Stage195
    scoped paper/repro refresh.
99. Treat Stage195 as scoped paper/repro refresh:
    `PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE`. The current exact full-MAT `T_bootstrap/r` evidence is ready
    for scoped reporting, but the broader research goal remains active and
    stronger claims remain blocked.
100. Treat Stage196 as public source refresh:
    `PASS_STAGE196_PUBLIC_SOURCE_REFRESH_METADATA_VISIBLE_FULLTEXT_REVIEW_BLOCKED`. Public metadata/code routes are visible, but theorem-level
    2025/686 citation review remains blocked by unavailable reviewed full text.
    No implementation branch opens from metadata alone.
101. Treat Stage197 as metadata-safe citation bank:
    `PASS_STAGE197_METADATA_SAFE_CITATION_BANK_READY_GOAL_ACTIVE`. Sentence-level writing support is now available, but
    theorem-level citation review, stronger novelty, compact implementation,
    and final optimality remain blocked.
102. Treat Stage198 as metadata-safe manuscript refresh:
    `PASS_STAGE198_METADATA_SAFE_MANUSCRIPT_REFRESH_READY_GOAL_ACTIVE`. A guarded scoped manuscript draft exists, with paragraph
    compliance and claim-guard tables. It is not a final paper and opens no
    new code branch.
103. Treat Stage199 as active goal verifier:
    `PASS_STAGE199_ACTIVE_GOAL_VERIFIER_RECORDED_GOAL_ACTIVE`. The requirement matrix keeps the goal active: scoped
    implementation evidence exists, while formal proof, full-text source
    anchors, and stronger completion claims remain incomplete.
104. Treat Stage200 as formal gap model with probe:
    `PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE`. R3 is improved from partial to a scoped model plus executable
    finite probes, but full goal completion remains open because source anchors
    and stronger implementation claims remain incomplete.
105. Treat Stage201 as structured selector distribution probe:
    `PASS_STAGE201_STRUCTURED_SELECTOR_DISTRIBUTION_PROBE_PROOF_ONLY`. The compact/shared-output route remains proof-only; dummy
    padding survives only simple public-pattern checks and still lacks semantic,
    resource, noise, and complete-SAB evidence.
106. Treat Stage202 as dummy padding semantic probe:
    `PASS_STAGE202_DUMMY_PADDING_SEMANTIC_PROBE_PROOF_ONLY`. Dummy padding is narrowed to a toy proof-only route with no
    key-size, security/noise, production keygen, or complete-SAB claim.
107. Treat Stage203 as production selector equation probe:
    `PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY`. A declared finite equation candidate passes phase and
    negative-control checks, but compact/shared-output SAB remains blocked on
    real keygen, security/noise, resource, and complete-SAB evidence.

108. Treat Stage204 as source anchor intake:
    `PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY`. Real public source
    metadata and implementation-environment constraints are recorded, but
    full-text theorem/equation anchors and production keygen evidence remain
    missing.

109. Treat Stage205 as current platform probe:
    `PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB`. Current-head scalar and
    explicit PVW paths pass WSL/spqlios_avx512 smoke; sequential r=2/r=4
    complete-SAB A/B is positive under `T_bootstrap/r`, but remains small-sample
    evidence and perf-counter attribution is blocked.

110. Treat Stage206 as current-head high-stat evidence:
    `PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE`. r=2/r=4 complete-SAB A/B
    has 10 correctness-passing samples under `T_bootstrap/r`, and r=2/r=4
    final-output noise has 20 seeds with zero PVW/scalar/pair failures. This
    remains current-head engineering evidence, not full theorem or novelty
    closure.
### Stage207 current-head resource refresh

`PASS_STAGE207_CURRENT_HEAD_RESOURCE_REFRESH` links Stage206 high-stat complete-SAB throughput to current-head
resource cost evidence. The goal remains active because profile attribution,
full-text theorem anchors, and broader branch/generalization gates remain open.
### Stage208 current-head profile attribution

`PASS_STAGE208_CURRENT_HEAD_PROFILE_ATTRIBUTION` records route-selection evidence only. The goal remains active:
the next executable route is a bounded MAT EP/from_DFT split or native-counter
gate, not another broad theory loop.
### Stage209 current-head MAT-EP split preflight

`PASS_STAGE209_CURRENT_HEAD_MAT_EP_SPLIT_PREFLIGHT` keeps the research loop executable: the next step is Stage210
candidate selection from measured split shares, not a broad theory loop or a
post-processing detour.
### Stage210 candidate admission

`PASS_STAGE210_SELECT_DFT_ROWS_PREFLIGHT_NO_HOTPATH_CODE` prevents theory drift and blind tuning: Stage211 must produce a
concrete DFT/FFT dataflow preflight or reject implementation permission.
### Stage211 FFT/DFT dataflow preflight

`PASS_STAGE211_DFT_DATAFLOW_PREFLIGHT_DENY_HOTPATH_CODE` prevents the optimization loop from drifting into repeated DFT
theory. The current code has no existing multirow DFT primitive; proceed to a
bounded Stage212 backend/API probe or native counter refresh.
### Stage212 multirow FFT API probe

`PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213` records whether a local multirow reverse-DFT wrapper is worth
carrying toward SAB integration. This keeps the loop executable and prevents
reopening DFT theory without measured evidence.
### Stage213 DFT wrapper integration preflight

`PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY` moves the loop from standalone backend evidence to guarded MAT-EP
integration evidence without claiming complete SAB speedup yet.
### Stage214 frontier native counter handoff

`PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY`: local hot-path candidates are closed or proof-gated; the next
executable route is Stage215 native hardware-counter execution using the
handoff script.
### Stage215 native counter execution

`PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN` updates the executable frontier after Stage214.
### Stage216 post-counter frontier

`PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT` closes the Stage215 DFT-wrapper route for now. The next valid work
is a compact selector keygen/security/noise preflight outside the SAB hot path,
or an external backend primitive if one is supplied. No new full-SAB speedup,
compact implementation, or optimality claim is opened by Stage216.
### Stage216 post-counter frontier

`PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT` closes the Stage215 DFT-wrapper route for now. The next valid work
is a compact selector keygen/security/noise preflight outside the SAB hot path,
or an external backend primitive if one is supplied. No new full-SAB speedup,
compact implementation, or optimality claim is opened by Stage216.
### Stage217 compact keygen/security preflight

`PASS_STAGE217_PATTERN_ONLY_KEYGEN_PREFLIGHT_NO_SAB_CODE` keeps the compact route executable but bounded. Count-matched
random dummy padding survives simple public-pattern probes, while row deletion,
deterministic zero dummy rows, and forced equal masks are rejected. No SAB
hot-path code or speedup claim is authorized.
### Stage218 compact key-object/noise prototype

`PASS_STAGE218_COMPACT_KEY_OBJECT_PROTOTYPE_READY_API_SKELETON` advances the compact route only to an isolated API-skeleton
candidate. It does not authorize `sab_pvw_*` integration, complete-SAB claims,
or production security/noise claims.
### Stage219 MOSFHET compact key API skeleton

`PASS_STAGE219_MOSFHET_COMPACT_KEY_API_SKELETON_READY_ENCRYPTED_KEYGEN` advances the compact route only to an encrypted-keygen prototype
candidate. It does not authorize `sab_pvw_*` integration, complete-SAB claims,
or production security/noise claims.
### Stage220 encrypted compact keygen prototype

`PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE` advances the compact route only to a production-noise recurrence
candidate. It does not authorize `sab_pvw_*` integration, complete-SAB claims,
or security claims.
- Stage221 compact keygen noise recurrence completed with `PASS_STAGE221_COMPACT_KEYGEN_NOISE_RECURRENCE_READY_ISOLATED_EP`. The next
  selected route is isolated compact external-product integration; `sab_pvw_*`
  remains untouched.
- Stage222 isolated compact EP integration completed with `FAIL_STAGE222`. The
  compact route remains outside SAB hot paths; the next decision is closed
  neighbor-capable compact state design versus exact PVW/MAT optimization.
- Stage223 route selection completed with `PASS_STAGE223_ROUTE_EXACT_PVW_MAT_REFRESH_SELECTED_COMPACT_COMPLETE_DENIED`. Next selected stage:
  Stage224 exact PVW/MAT AVX/resource refresh measured by `T_bootstrap/r`.
- Stage224 exact PVW/MAT AVX refresh completed with `PASS_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_POSITIVE`. Continue with
  fresh noise/resource rerun only if this refresh is promoted beyond Stage148.
- Stage225 exact refresh noise/resource completed with `PASS_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE`. The next
  selected route is counter attribution for the exact MAT/PVW backend gain.
### Stage226 exact counter attribution

`PASS_STAGE226_COUNTERS_RECORDED_TIMING_NEUTRAL` updates the mechanism evidence for the exact dense MAT/PVW route.
### Stage227 exact route claim boundary

`PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED` separates supported exact-route results from blocked optimality, compact-route and novelty claims.
### Stage228 counter-driven backend kernel search

`PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX` prevents blind exact-path retuning and routes to parameter generalization.
### Stage229 parameter generalization matrix

`PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED` fixes the exact-route parameter matrix and keeps non-binary, all-parameter, novelty, and theoretical-optimality claims out of scope until their gates run.
### Stage230 source-verified literature novelty audit

`PASS_STAGE230_SOURCE_VERIFIED_SCOPED_NOVELTY_BOUNDARY` refreshes real-source related-work boundaries. Continue only with current-head parameter refresh, scoped manuscript skeleton, or separately gated non-binary/compact design.
### Stage231 current-head added-parameter refresh

`PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING` records current-head added-parameter smoke continuity. Do not promote added parameters into a current-head paper table until Stage232 full-stat/resource gates run.
### Stage232 selected current-head preflight

`PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING` records a bounded executable step after Stage231. The goal remains
active: Stage232 is selected-subset preflight evidence only; full matrix
high-statistics and manuscript packaging remain open.
### Stage233 first high-stat added-parameter slice

`PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING` records the first current-head added-parameter high-stat slice.
The active goal remains open because the remaining matrix slices, manuscript
packaging, and broader optimality/theory gates are not complete.
### Stage234 second high-stat added-parameter slice

`PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING` records the second current-head added-parameter high-stat slice.
The active goal remains open because `SET_2_3_4096` high-stat slices,
manuscript packaging, and broader optimality/theory gates are not complete.
### Stage235 SET_2_3_4096 r=2 high-stat slice

`PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING` records the third current-head added-parameter high-stat slice.
The active goal remains open because `SET_2_3_4096`, r=4 high-stat evidence,
manuscript packaging, and broader optimality/theory gates are not complete.
### Stage236 selected binary added-parameter matrix complete

`PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE` records the fourth current-head added-parameter high-stat slice.
The selected binary matrix is now complete for `SET_4_5_2048` and
`SET_2_3_4096`, r=2/r=4. The active goal remains open for manuscript packaging,
source-grounded novelty boundaries, and any broader design routes.
### Stage237 scoped manuscript package

`PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED` records a paper-facing package for the selected binary exact dense
PVW/MAT-SAB result. The goal remains active because final citation verification,
venue-specific paper assembly, optional native-counter attribution, and broader
algorithmic gates remain incomplete.
### Stage238 source-verified citation package

`PASS_STAGE238_SOURCE_VERIFIED_CITATION_PACKAGE_READY_NO_BIBTEX_HALLUCINATION` records source/claim support for the scoped manuscript package.
The active goal remains open because final BibTeX retrieval, venue-specific
paper assembly, optional native-counter attribution, and broader proof gates
remain incomplete.
### Stage239 verified BibTeX retrieval and LaTeX stub

`PASS_STAGE239_PARTIAL_VERIFIED_BIBTEX_LATEX_STUB_READY_TODOS_REMAIN` records partial verified BibTeX retrieval and a minimal LaTeX
stub. The active goal remains open because final bibliography closure,
venue-specific paper assembly, optional native-counter attribution, and broader
algorithmic gates remain incomplete.
### Stage240 scoped LaTeX draft

`PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED` records a scoped LaTeX draft using Stage236 experiments and
Stage239 verified citations. The active goal remains open because final paper
compilation, unresolved BibTeX rows, optional counter refresh, non-binary
support, compact route, and theoretical optimality remain incomplete.
### Stage241 LaTeX compile package

`PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY` records successful compile/package evidence for the scoped draft.
The active goal remains open because unresolved bibliography rows, optional
current-head counter refresh, non-binary support, compact route, and theoretical
optimality remain incomplete.
### Stage242 unresolved BibTeX follow-up

`PASS_STAGE242_BIBTEX_TODO_REDUCED_BATCHBOOT_REMAINS` records partial bibliography closure. The active goal remains open
because BatchBoot final citation closure, draft patch/recompile, optional
counter refresh, non-binary support, compact route, and theoretical optimality
remain incomplete.
