# Roadmap: Stage 19+ PVW/MAT-SAB Acceleration

Date: 2026-06-25

This roadmap supersedes the open Stage 19+ section of
`docs/stage16_plus_execution_plan.md` after Stage 18 concluded that fused
from-DFT-add is a neutral ablation. The next work must target full SAB
throughput by reducing schedule, buffer, layout, and post-processing costs
around the MAT external product.

## Stage 19: Exact Sparse Schedule Audit

Goal:

```text
Make the SAB sparse schedule, CMUX/NCMUX counts, copyback count, sub_a count,
and per-stage timing exact enough to guide optimization.
```

Theory basis:

- target primary shape: `BINARY SET_2_3_2048`;
- `in_N = 2048`, `r_prec = 7`, `h + 1 = 40`;
- each RGSW monomial step performs `r_prec * in_N = 14336`
  CMUX/NCMUX-class updates;
- expected total external-product-class updates:
  `(h + 1) * r_prec * in_N = 40 * 7 * 2048 = 573440`;
- NCMUX count per monomial is `sum_{b=0}^{r_prec-1} 2^b = 127`, so the target
  total is `5080`.

Code tasks:

- add a schedule-audit profile mode or extend `SAB_PVW_BODY_PROFILE`;
- emit per-r and per-run counters for:
  `rgsw_monomial_calls`, `cmux_calls`, `ncmux_calls`, `mat_ep_calls`,
  `sub_a_calls`, `copyback_calls`, and per-bit CMUX/NCMUX counts;
- emit per-stage timing for MAT EP, CMUX wrapper, from_DFT, add/sub, NCMUX
  automorphism, sub_a, copyback, setup, extract, and key switching;
- do not use instrumented timing as final latency evidence.

Correctness gate:

- `SAB_PVW_BENCH correctness target_full Pass` for every profiled run;
- counter integrity:
  `cmux_calls == mat_ep_calls == 573440` on the target full-body path;
- NCMUX count matches the expected `5080` target value for the binary path.

Performance gate:

- produce a ranked cost table that identifies the next optimization target;
- if counters or timing do not match the static model, stop and fix the model.

Artifacts:

- `experiments/stage19_sparse_schedule_audit_plan.md`;
- `repro/stage19_sparse_schedule_profile_*/summary.csv`;
- `docs/stage19_sparse_schedule_audit_log.md`;
- updates to `hypotheses/hypothesis_register.yaml`.

## Stage 20: RGSW Monomial Active-Buffer Fusion

Goal:

```text
Avoid forced buffer normalization after each RGSW monomial when the next SAB
step can consume the active ping-pong buffer directly.
```

Theory basis:

The current RGSW monomial logic uses a ping-pong accumulator through the
`r_prec` butterfly layers. Because `r_prec = 7` is odd in the target parameter,
each call must normalize or copy back before returning to the caller. Across
`h + 1 = 40` sparse steps, this creates repeated traffic that is not part of
the mathematical blind rotation.

Code tasks:

- introduce an internal state structure carrying:
  active PVW buffer pointer, inactive scratch pointer, parity, lane count, and
  parameter metadata;
- add an internal `sab_pvw_RGSW_monomial_mul_state` path that returns active
  state rather than forcing copyback;
- let `sparse_mul` and `sub_a` consume the active state;
- normalize only at API boundaries, extract boundaries, or explicit debug
  checkpoints;
- preserve the old copyback path as the reference implementation.

Correctness gate:

- staged RGSW monomial lane equivalence for `r=1/2/4`;
- isolated sparse_mul equivalence;
- bootstrap-without-extract equivalence;
- full target output equivalence.

Performance gate:

- repeated full SAB A/B for `r=2` and `r=4`;
- body profile must show lower copyback and schedule traffic;
- promotion requires a stable full SAB improvement over Stage 16 under the same
  backend.

Failure handling:

- if correctness fails, disable the state path and preserve logs;
- if micro profile improves but full SAB does not, keep as neutral ablation;
- if only one r value improves, scope the variant to that r value.

## Stage 21: sub_a and Polynomial Rotation Optimization

Goal:

```text
Reduce `sub_a` and monomial rotation overhead without changing SAB semantics.
```

Theory basis:

`sub_a` depends on encrypted input-derived rotation exponents and cannot be
treated as a static schedule. Optimization is therefore limited to safe scratch
reuse, vectorized copy/negation, reduced metadata work, and active-buffer
handoff from Stage 20.

Code tasks:

- audit `pvmtmlwe_mul_by_xai` for aliasing and scratch requirements;
- add scratch-aware rotation only if the source and destination safety
  conditions are explicit;
- split profile timing into index arithmetic, coefficient copy, sign handling,
  and body-lane loops;
- do not add in-place rotation unless it is proven not to overwrite unread
  coefficients.

Correctness gate:

- per-step phase equivalence against scalar reference;
- target full-output correctness;
- multi-seed correctness if the path is promoted.

Performance gate:

- full SAB A/B must improve over the active-buffer baseline;
- if `sub_a` remains a small fraction after Stage 20, defer deeper work.

Status after execution:

```text
Implemented SAB_PVW_SUBA_OUTPUT_FUSION=true as an explicit ablation.
Correctness and count gates passed for r=2/r=4.
Sequential one-run full SAB smokes did not improve over the Stage 20 repeated
baseline, so the path is recorded as neutral and is not promoted.
```

## Stage 22: MAT-Aware AVX512 Theoretical-Limit Audit

Goal:

```text
Determine whether the current MAT external product AVX512 implementation is
near the useful theoretical limit for r=2/r=4, and identify any remaining
layout or register-tiling opportunities.
```

Theory basis:

For `k=1,l=1`, MAT uses `m = k + r = 1 + r` rows and outputs. A repeated scalar
path costs roughly `4r` complex products, while dense MAT costs `m^2`. MAT can
reduce shared-mask decomposition and output traffic, but r=4 pays `25` dense
products versus `16` repeated scalar products.

Code tasks:

- preserve both generic single-poly AVX and MAT-aware AVX paths;
- add reproducible microbench commands comparing both under the same binary
  configuration;
- inspect assembly and, where available, perf counters for loads, stores, FMA,
  retired instructions, cycles, and cache behavior;
- test r=2 register-resident accumulation and r=4 lower-pressure tiling only
  behind explicit flags;
- avoid changing key layout unless the experiment is isolated and reversible.

Correctness gate:

- staged MAT/PVW tests for `r=1/2/4`;
- target full-output correctness for any promoted AVX512 path.

Performance gate:

- microbench must show expected memory-operation reduction;
- full SAB repeated A/B must also improve before any bootstrapping claim;
- backend gains must be separated from algorithmic gains.

Status after execution:

```text
Generic-vs-specialized same-backend audit completed.
For r=4 full SAB with active-buffer fusion, specialized MAT-AVX512 improved
PVW latency over generic MAT-AVX512 by 1.040x over three process runs.
This supports the explicit specialized kernel as the current practical path,
but not a theoretical-optimality claim because hardware perf counters were not
captured and dense MAT multiply cost remains visible.
```

## Stage 23: PVW CMUX/NCMUX Schedule Fusion

Goal:

```text
Fuse above individual CMUX calls by exploiting per-bit and per-monomial SAB
butterfly structure.
```

Theory basis:

Stage 18 showed that local from-DFT-add fusion is correct but neutral at full
SAB level. The next candidate should reduce lifetime and traffic across CMUX
groups rather than only within one CMUX epilogue.

Code tasks:

- carry lane state across CMUX/NCMUX groups;
- reduce intermediate DFT materialization when a following add/sub consumes it
  immediately;
- precompute per-bit index ranges and dispatch metadata;
- compare schedule-level fusion against Stage 18 fused from-DFT-add to avoid
  duplicate neutral work.

Correctness gate:

- per-CMUX phase equality for each PVW body lane;
- full target output equivalence;
- scalar path regression pass.

Performance gate:

- full SAB repeated A/B for `r=4` first, then `r=2`;
- promote only if Stage 16/18 full SAB means improve beyond run variability.

Status after execution:

```text
Implemented SAB_PVW_SCHEDULE_FUSED_CMUX=true as an explicit schedule-local
ablation. The path preserves target full-output correctness and exact schedule
counts for r=2/r=4: CMUX/MAT EP 573440, NCMUX 5080, schedule-fused direct
CMUX 568360, and copyback 0 with active-buffer fusion.

Sequential three-run full SAB A/B did not improve over the current best
experimental path. r=2 averaged 1.273x, essentially tied with Stage 20's
1.270x. r=4 averaged 1.335x, below Stage 20's 1.346x and Stage 22's 1.373x.
The candidate is therefore recorded as neutral and is not promoted.
```

## Stage 24: Conditional Post-Processing Optimization

Goal:

```text
Optimize extract, packing KS, or HW-KS only if the body path has been improved
enough that post-processing becomes material.
```

Code tasks:

- re-run post-processing profile after promoted body changes;
- if the tail remains near 1%, keep direct-to-packing KS deferred;
- if the tail is material, implement PVW-aware direct-to-packing KS behind a
  flag and compare against scalar per-lane post-processing.

Gate:

- no high-risk post-processing change is accepted without full-output
  equivalence and resource reporting.

Status after execution:

```text
Stage 24 re-measured the tail under the current promoted experimental body
path: spqlios_avx512, specialized MAT-AVX512, and active-buffer fusion. The
maximum observed post-processing tail was 1.261195%, with mean tail 1.105833%
across r=2/r=4 samples. This is below the 2.0% implementation threshold, so
direct-to-packing KS and batched extract are deferred. The next stage is the
correctness/noise/resource matrix for the current best explicit path.
```

## Stage 25: Correctness, Noise, and Resource Matrix

Goal:

```text
Convert promoted variants into robust engineering evidence.
```

Required matrix:

- `r in {1,2,4}`;
- same-backend full SAB A/B;
- deterministic multi-seed correctness;
- stage-level and final-output noise;
- key size, keygen time, RSS, and scratch memory;
- raw logs for failures, neutral runs, and accepted runs.

Gate:

- failure rate must not exceed scalar baseline under the same tested scope;
- noise growth must be bounded or explicitly explained;
- resource overhead must be reported with speedup.

Status after initial execution:

```text
Initial smoke-level Stage 25 matrix completed for the current best explicit
path: spqlios_avx512, MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true, and
SAB_PVW_ACTIVE_BUFFER_FUSION=true. Final-output noise, stage-level noise, and
resource scripts now cover r=1/2/4. One deterministic seed passed with zero
PVW, scalar, and pair failures at final output; stage probes also reported
zero pair failures across blind_rotate_coeff0, extract, materialize_tlwe,
packing_ks, and hw_ks. Resource reporting shows PVW estimated public key bytes
at 1.000029x, 1.013617x, and 1.065349x repeated scalar for r=1/2/4,
respectively. PVW keygen is slower per lane in this smoke run, so keygen cost
must be reported with any throughput claim.

The 50-seed final-output expansion then passed for promoted r=2 and r=4:
r=2 had 50 seeds, 204800 points, and zero PVW/scalar/pair failures; r=4 had
50 seeds, 409600 points, and zero PVW/scalar/pair failures. PVW-vs-scalar
log2 sigma gaps stayed within [-0.446, 0.619] for r=2 and [-0.555, 0.682]
for r=4, below the configured 4.0 threshold.

This closes the Stage 25 final-output noise expansion for the target path.
Stage-level noise is still smoke-level, and Stage 26 parameter/branch
generalization remains required before any broad SAB claim.
```

## Stage 26: Parameter and Branch Generalization

Goal:

```text
Define how far the result generalizes beyond BINARY SET_2_3_2048.
```

Tasks:

- add at least one smaller smoke parameter and one target parameter;
- check binary, ternary, and include-zero branches only if claimed;
- record how `N`, `h`, `r_prec`, backend, and r affect speedup;
- keep unsupported branches explicitly out of scope.

Gate:

- no broad SAB claim may rely on only one parameter set.

Status after initial execution:

```text
Stage 26 first fixed the PVW target harness so PARAM=SET_* actually changes
the PVW target, bench, noise, stage-noise, and resource gate parameters.
Previously those paths were hard-coded to BINARY SET_2_3_2048.

Initial binary parameter smoke passed for SET_2_3_2048, SET_4_5_2048, and
SET_2_3_4096 under spqlios_avx512 with specialized MAT-AVX512 and
active-buffer fusion. The corresponding h/r_prec values were 39/7, 42/7, and
32/8. PVW+TERNARY is now explicitly rejected as unsupported, while scalar
TERNARY still builds.

This supports binary parameter-smoke generalization only. It does not yet
support non-binary PVW-SAB, repeated performance scaling claims on the new
parameters, or noise robustness beyond smoke-level added-parameter gates.

Follow-up execution added initial performance/noise smoke for the added binary
parameters. Under `spqlios_avx512`, specialized MAT-AVX512, and active-buffer
fusion, `SET_4_5_2048` r=2 reached 1.310x and r=4 reached 1.437x in one-run
complete-SAB A/B smokes; `SET_2_3_4096` r=2 reached 1.251x and r=4 reached
1.359x. All corresponding one-seed final-output noise smokes had zero PVW,
scalar, and pair failures. This strengthens parameter smoke, but does not yet
support broad statistical performance/noise claims.

`SET_4_5_2048` r=4 was then expanded to a 3-run/3-seed repeated smoke. The
complete-SAB A/B mean speedup was 1.360x with range 1.352x-1.376x, and all
24576 final-output noise points had zero PVW, scalar, and pair failures. This
supports a scoped repeated-smoke claim for that added parameter, still below
the main-target 50-seed evidence level.

`SET_2_3_4096` r=4 was also expanded to a 3-run/3-seed repeated smoke. The
complete-SAB A/B mean speedup was 1.317x with range 1.270x-1.346x, and all
49152 final-output noise points had zero PVW, scalar, and pair failures. This
adds repeated-smoke support for the larger `in_N=4096`, `r_prec=8` binary
parameter.

The added-parameter r=2 cases were then expanded to the same 3-run/3-seed
repeated-smoke level. `SET_4_5_2048` r=2 reached mean speedup 1.238x with
range 1.086x-1.434x, and all 12288 final-output noise points had zero PVW,
scalar, and pair failures. `SET_2_3_4096` r=2 reached mean speedup 1.227x with
range 1.219x-1.235x, and all 24576 final-output noise points had zero PVW,
scalar, and pair failures. The added binary parameters therefore have
repeated-smoke support for r=2 and r=4, but not the main-target 50-seed noise
level.

The added binary parameter matrix was then expanded to 5 full-SAB A/B runs and
5 final-output noise seeds for `SET_4_5_2048` and `SET_2_3_4096`, r=2/r=4.
All full-SAB correctness gates passed and all noise aggregates had zero PVW,
scalar, and pair failures. Mean speedups were: `SET_4_5_2048` r=2 1.329x,
r=4 1.346x; `SET_2_3_4096` r=2 1.224x, r=4 1.318x. This is the strongest
current added-parameter support, but it remains small-sample evidence and does
not replace the main target's 50-seed noise gate. `SET_4_5_2048` r=2 has high
run-to-run variance and must be reported with its range or confidence interval.
```

## Stage 27: Novelty and Paper Package

Goal:

```text
Turn the engineering result into a scoped, citation-safe paper claim only if
the evidence supports it.
```

Tasks:

- build a related-work matrix for 2025/686 SAB, PVW/MAT external products,
  multi-output bootstrapping, amortized bootstrapping, and SIMD FHE kernels;
- label every claim as theory-supported, experiment-supported, engineering
  only, neutral, or failed;
- prepare algorithm description, complexity model, correctness/noise
  discussion, benchmark tables, ablations, limitations, and reproduction pack.

Gate:

- no complete-SAB speedup claim without full SAB benchmark support;
- no novelty claim without literature support.

Status after initial execution:

```text
Stage 27 initial related-work and claim-boundary audit is complete enough to
set the paper framing. The current safe claim is an engineering/systems
optimization: PVW/MAT shared-mask multi-body batching is integrated into the
2025/686 binary SAB implementation with complete-SAB performance evidence and
noise/resource gates under tested scope.

Novelty is not yet claimable. 2025/2112 common-mask TFHE has strong overlap
with shared-mask multiple-body ciphertexts and distinct LUT support, so this
project must not claim invention of the shared-mask batching idea. The open
paper contribution, if any, must be SAB-specific integration, schedule
engineering, implementation evidence, or a clearly distinguished algorithmic
delta after full paper review.

The first final full-SAB performance rerun after Stage 26 parameterized the
harness also completed. Under `spqlios_avx512`, specialized MAT-AVX512, and
active-buffer fusion, r=2 averaged 1.171x over three runs and r=4 averaged
1.401x over three runs. This strengthens the scoped engineering performance
claim for the current promoted path but does not change the novelty boundary.

The related-work refresh then added a source-access matrix and claim-support
matrix. It strengthens the safe engineering claim and makes the novelty block
more explicit: 2025/2112 common-mask/shared-mask multiple-body TFHE remains a
strong prior-art risk for shared-mask batching, while 2025/686 full text is
still required before theorem-level base-paper citations can be written.

The final scoped engineering evidence package was then generated by
`scripts/build_stage27_final_package.py`. It aggregates Stage 25/26/27
performance, final-output noise, resource, and claim-boundary evidence into
`docs/stage27_final_evidence_package.md` and
`repro/stage27_final_evidence_package/`. This closes the engineering package
assembly for the safe scoped claim, but not novelty or theorem-level citation
review.

A reproducible citation-access probe was also added for 2025/686. It confirms
that ePrint, ACM, and ResearchGate direct full-text routes are blocked in the
current environment, while Semantic Scholar and DBLP provide metadata only.
The theorem-level citation gate therefore remains blocked until the full paper
is manually supplied and inspected.

Finally, the completion-readiness audit maps the final standards and Stage
19-27 items to concrete evidence. It marks the scoped engineering evidence
chain ready and identifies the remaining work as stronger-claim work:
full-paper citation review, novelty review, non-binary PVW design, broader
parameter statistics, native perf counters for theoretical AVX512 claims, or
stage-level noise expansion if such claims are introduced.

The final scoped engineering report is recorded in
`docs/stage27_final_engineering_report.md`. It is the current presentation
layer for the completed engineering evidence chain and keeps the stronger
claims blocked.
```

## Stage 28: Native Perf-Counter Gate

Goal:

```text
Determine whether the current platform can support hardware-counter-backed
MAT-AVX512 load/store attribution, which is required before upgrading the
Stage 22 practical SIMD result into a theoretical-optimality claim.
```

Tasks:

- record CPU, WSL/native platform, `perf` availability, and
  `perf_event_paranoid`;
- run a lightweight `perf stat` smoke if `perf` exists;
- only run the heavy r=4 SAB benchmark under counters when
  `STAGE28_RUN_BENCH=1`;
- preserve blocked results as evidence instead of silently treating Stage 22
  objdump evidence as hardware-counter evidence.

Gate:

- `perf` must be in PATH;
- basic `perf stat` must pass;
- heavy r=4 SAB benchmark must pass target-full correctness if executed;
- otherwise MAT-AVX512 theoretical load/store claims remain blocked.

Status after initial execution:

```text
Stage 28 lightweight gate was run in the current WSL2 environment. It recorded
AVX512-capable CPU flags and `perf_event_paranoid=2`, but Linux `perf` was not
available in PATH. The hardware-counter gate is therefore blocked on this
platform. This does not change the scoped engineering speedup claim, but it
does keep MAT-AVX512 theoretical load/store optimality blocked until a
native/perf-enabled run is available.
```

## Stage 29: Final Goal Completion Audit

Goal:

```text
Convert the current Stage 19+ evidence chain into a machine-generated
completion audit that distinguishes scoped engineering completion from
stronger blocked claims.
```

Tasks:

- read the Stage 27 final package CSVs;
- read Stage 27 completion readiness;
- read Stage 28 native perf-counter gate;
- check target complete-SAB speedup, target 50-seed final-output noise,
  resource reporting, manifest existence, blocked-claim preservation, and
  added-parameter small-sample support;
- emit a final audit CSV and Markdown summary.

Gate:

- every scoped engineering item must be backed by current artifacts;
- blocked novelty, theorem-level citation, non-binary, all-parameter, and
  MAT-AVX512 theoretical-optimality claims must stay blocked unless stronger
  evidence is supplied;
- the audit must not mark the active goal complete when stronger-claim evidence
  remains external or unavailable.

Status after initial execution:

```text
`scripts/build_final_goal_completion_audit.py` generated
`repro/final_goal_completion_audit.csv` and
`docs/final_goal_completion_audit.md`.

Decision:
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED

The scoped engineering acceleration evidence chain is ready and reproducible,
but novelty, theorem-level 2025/686 citations, non-binary support, broad
all-parameter support, and MAT-AVX512 hardware-counter optimality remain
blocked or conditional.
```

## Stage 30: Final Goal Recheck Runner

Goal:

```text
Provide a single reproducible command that refreshes the current external-gate
state and final audit without changing the scalar or PVW/MAT-SAB
implementation.
```

Tasks:

- optionally refresh the Stage 27 citation/full-text probe;
- refresh the Stage 28 native perf-counter gate;
- rebuild the Stage 27 final evidence package;
- regenerate the Stage 29 final goal completion audit;
- record the final `A9` decision in a recheck summary CSV.

Gate:

- default recheck must not run expensive or network-dependent checks unless
  explicitly requested;
- skipped citation probing must not be interpreted as theorem-level citation
  support;
- blocked perf-counter probing must not be interpreted as theoretical
  MAT-AVX512 optimality support.

Status after initial execution:

```text
`bash scripts/run_final_goal_recheck.sh` completed with citation probing
skipped, Stage 28 perf gate refreshed, final package rebuilt, external evidence
intake refreshed, and final goal audit regenerated.

Decision:
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

## Stage 31: External Evidence Intake

Goal:

```text
Register externally supplied full-text and native/perf evidence with hashes and
claim-safe status labels, without automatically upgrading manuscript claims.
```

Tasks:

- register a locally supplied 2025/686 PDF/text artifact when
  `FAB686_FULLTEXT_PATH` is provided;
- register a native/perf-enabled Stage 28 summary when
  `STAGE28_NATIVE_PERF_SUMMARY` is provided;
- record missing evidence when no external paths are supplied;
- feed the external intake result into the final goal completion audit.

Gate:

- file paths must exist before being recorded as available;
- PDF/text detection and SHA-256 hashes must be recorded;
- external evidence may only change the audit to review-required, not complete.

Status after initial execution:

```text
`scripts/register_external_evidence.py` generated
`repro/external_evidence_intake/summary.csv`.

Current status:
fab686_fulltext = MISSING
stage28_native_perf_summary = MISSING

The final goal audit now includes A8b for optional external evidence. Since no
external files were supplied, the final decision remains:
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

## Stage 32: Citation Refresh Recheck

Goal:

```text
Refresh the external 2025/686 full-text gate and propagate the result through
the final recheck and final goal audit.
```

Tasks:

- run `FINAL_RECHECK_CITATION=1 bash scripts/run_final_goal_recheck.sh`;
- preserve citation-probe logs;
- inspect direct PDF and metadata-only outcomes;
- keep theorem-level citation claims blocked unless direct full text is
  available and later manually reviewed.

Gate:

- `stage27_citation_probe` must pass as a command;
- `direct_pdf_access` must be `PASS` before theorem-level citation review can
  start;
- final audit must remain scoped-ready/blocked when only metadata or HTTP 403
  results are observed.

Status after initial execution:

```text
The 2026-06-26 refresh ran successfully. Direct PDF access remains blocked:
ePrint HTML/PDF, ACM DOI/PDF, and ResearchGate returned 403; Semantic Scholar
and DBLP provide metadata only. The final recheck decision remains:

SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED
```

## Stage 33: Current Commit Smoke

Goal:

```text
Refresh current-commit scalar baseline and explicit PVW target correctness
evidence after the final package and recheck orchestration work.
```

Tasks:

- run the default scalar binary full SAB path on `SET_2_3_2048`;
- run the explicit `SAB_PVW_TARGET_TEST` target full lane-equivalence gate;
- build the scalar ternary path to confirm the PVW binary-only guard did not
  break non-binary scalar compilation;
- feed the smoke summary into the final goal completion audit.

Gate:

- scalar binary run must end with `Pass`;
- PVW target gate must report `SAB_PVW target full bootstrap gate: Pass`;
- scalar ternary build must pass;
- results are correctness/build smoke only, not performance evidence.

Status after initial execution:

```text
`bash scripts/run_stage33_current_smoke.sh` passed all three gates under
`spqlios_avx512` and `SET_2_3_2048`. The final goal audit now includes A5b:

PASS_CURRENT_SMOKE
```

## Stage 34: Current-Smoke Final Recheck Integration

Goal:

```text
Make the Stage 33 current-commit scalar/PVW smoke gate refreshable through the
single final-goal recheck command before the generated final audit is rebuilt.
```

Tasks:

- add `FINAL_RECHECK_CURRENT_SMOKE=1` support to
  `scripts/run_final_goal_recheck.sh`;
- keep the default lightweight recheck fast by skipping current smoke unless
  explicitly requested;
- run the Stage 33 smoke before final audit generation when enabled;
- record the result in `repro/final_goal_recheck/summary.csv` and
  `repro/final_goal_recheck/stage33_current_smoke.log`;
- preserve the rule that the smoke is build/correctness evidence only, not a
  performance claim.

Gate:

- `bash -n scripts/run_final_goal_recheck.sh` must pass;
- `FINAL_RECHECK_CURRENT_SMOKE=1 bash scripts/run_final_goal_recheck.sh` must
  pass with `stage33_current_smoke=PASS`;
- the regenerated final audit must keep `A5b=PASS_CURRENT_SMOKE`;
- the final decision must remain scoped-ready/stronger-blocked unless external
  stronger evidence is supplied.

Status:

```text
Implementation and execution completed. The final recheck runner now accepts
FINAL_RECHECK_CURRENT_SMOKE=1, records stage33_current_smoke=PASS in
repro/final_goal_recheck/summary.csv, regenerates the final audit afterward,
and preserves the final decision:
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED.
```

## Stage 35: Completion Blocker Matrix

Goal:

```text
Convert the final goal audit into an explicit remaining-work matrix that
distinguishes scoped-complete evidence, optional expansions, claim guardrails,
and external blockers.
```

Tasks:

- read `repro/final_goal_completion_audit.csv`;
- read optional external-evidence intake state;
- classify every final audit row into:
  `complete_or_scoped_complete`, `optional_expansion`, `claim_guardrail`,
  `external_blocker`, or `overall_scoped_ready`;
- emit a machine-readable CSV and a Markdown log;
- keep stronger claims blocked unless external artifacts or expanded evidence
  are actually supplied.

Gate:

- every final audit row must be represented in the Stage 35 matrix;
- `A8` and `A8b` must remain external blockers in the current environment;
- `A9` must remain scoped-ready/stronger-blocked.

Status:

```text
Stage 35 completed. The generated matrix covers all final audit rows:
5 scoped-complete items, 2 optional expansions, 1 claim guardrail,
2 external blockers, and 1 overall scoped-ready decision. The current external
blockers remain fab686_fulltext=MISSING and
stage28_native_perf_summary=MISSING.
```

## Stage 36: High-Statistics Claim Expansion

Goal:

```text
Only if broad or paper-level statistical wording is required, expand target
and added-parameter performance/noise/resource evidence beyond the current
scoped engineering package.
```

Tasks:

- define run/seed budgets before execution;
- rerun target full-SAB A/B for promoted r=2/r=4 under one backend;
- optionally expand Stage 25 stage-level noise beyond smoke;
- optionally expand Stage 26 added-parameter runs/seeds beyond 5-run/5-seed
  support;
- record confidence intervals and failure statistics.

Gate:

- no single-run result may upgrade a claim;
- resource and noise must be reported with performance;
- this stage is optional for the current scoped engineering claim and required
  only for broader statistical claims.

## Stage 37: Native Perf-Counter Evidence

Goal:

```text
Run MAT-AVX512 load/store/FMA attribution on native Linux or a perf-enabled
WSL environment.
```

Tasks:

- run Stage 28 with `STAGE28_RUN_BENCH=1`;
- collect hardware counters for generic and specialized MAT paths;
- register the resulting summary through `STAGE28_NATIVE_PERF_SUMMARY`;
- rerun final recheck.

Gate:

- `perf stat` must run successfully;
- target full-SAB correctness must pass during any heavy benchmark;
- without this evidence, theoretical MAT-AVX512 load/store optimality remains
  blocked.

## Stage 38: Full 2025/686 Source Review

Goal:

```text
Review the full 2025/686 paper before writing theorem-level SAB protocol
claims or asserting novelty relative to the base paper.
```

Tasks:

- provide the full paper through `FAB686_FULLTEXT_PATH`;
- register the artifact and hash;
- map every protocol/theorem claim in the report to page/section evidence;
- update related-work and claim-support matrices.

Gate:

- metadata-only access is insufficient;
- no theorem-level manuscript citation may be upgraded before full-text review;
- novelty remains blocked if related work already covers the claimed idea.

## Stage 39: Optional New Algorithmic Variants

Goal:

```text
Pursue new acceleration only if the desired scope is beyond the current
promoted active-buffer MAT-SAB engineering result.
```

Candidate directions:

- non-binary PVW-SAB branch support;
- deeper sparse-schedule fusion beyond the neutral Stage 23 attempt;
- MAT key/layout experiments that reduce r=4 dense-matrix pressure;
- direct post-processing only if a new profile shows a larger tail;
- AVX512 r-specific kernels backed by native counters.

Gate:

- every candidate starts as explicit-flag experimental code;
- scalar SAB remains unchanged;
- full SAB A/B, correctness, noise, and resource gates are required before
  promotion.

## Stage 40: Final Paper/Release Freeze

Goal:

```text
Freeze the exact claim scope, reproducibility pack, and manuscript/release
artifacts after all selected blockers or expansions are resolved.
```

Tasks:

- rerun final recheck with all selected gates enabled;
- regenerate final package, final audit, and blocker matrix;
- freeze claim-support wording;
- produce final paper/report artifacts with no blocked claims written as
  completed claims.

Gate:

- final audit must match the selected scope;
- no stronger claim can be included without its corresponding Stage 36-39
  evidence.
