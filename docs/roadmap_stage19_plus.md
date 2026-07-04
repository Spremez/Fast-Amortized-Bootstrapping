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
r=4 1.346x; `SET_2_3_4096` r=2 1.224x, r=4 1.318x. This was later superseded
by the Stage 36 added-binary 10-run/20-seed campaign. The Stage 26 matrix
remains useful as an earlier smoke and harness checkpoint, but it should no
longer be described as the strongest added-parameter evidence.
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
  added-parameter 10-run/20-seed support when available;
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
Stage 35 completed and was refreshed after Stage 36. The generated matrix now
covers all final audit rows: 5 scoped-complete items, 4 statistical
expansions, 1 optional expansion, 1 claim guardrail, 2 external blockers, and
1 overall scoped-ready decision. The current external blockers remain
fab686_fulltext=MISSING and stage28_native_perf_summary=MISSING.
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

Status:

```text
Stage 36 plan generation completed. The high-priority target_perf campaign was
executed: r=2 mean speedup 1.191x with 95% CI [1.075307, 1.306693], and r=4
mean speedup 1.377x with 95% CI [1.314893, 1.438107]. The original long command
hit a tool timeout while WSL-side artifacts completed; two later r=4 top-up
runs are preserved as supplemental and not included in the primary 10-run
statistic.

The stage_noise campaign was also executed for r=2/r=4 with 10 deterministic
seeds. All reported stages passed with zero pair failures:
blind_rotate_coeff0, extract, materialize_tlwe, packing_ks, and hw_ks.

The target_noise campaign was then executed for the target promoted path with
50 deterministic seeds for r=2 and r=4. Both target r values passed with zero
PVW, scalar, and pair final-output failures. r=2 covered 204800 points with
PVW-minus-scalar log2 gap range [-0.446, 0.619], and r=4 covered 409600 points
with gap range [-0.555, 0.682].

The resource campaign was executed three times for scalar and PVW r=1/2/4
after switching benchmark timing to CLOCK_MONOTONIC to avoid wall-clock
underflow in resource logs. All six scalar/PVW r/mode groups have three
samples and PASS_RESOURCE_3RUN. PVW public key byte ratios versus repeated
scalar remain 1.000029x for r=1, 1.013617x for r=2, and 1.065349x for r=4.

The added-parameter campaign was then executed for `SET_4_5_2048` and
`SET_2_3_4096`, r=2/r=4. Each parameter/r case now has 10 complete-SAB
same-backend performance samples and 20 deterministic final-output noise seeds.
Mean speedups are `SET_4_5_2048` r=2 1.286x, r=4 1.351x; `SET_2_3_4096`
r=2 1.235x, r=4 1.346x. The t-intervals are fully above 1.0 for all four
cases, and all reported PVW, scalar, and pair noise failures are zero. The
initial all-in-one command hit a tool timeout after producing partial
artifacts, so `SET_2_3_4096` r=4 was completed by a targeted top-up. Two
extra r=4 top-up samples are recorded as supplemental and excluded from the
primary 10-run statistic.

This strengthens target-performance, refreshed target final-output noise,
stage-level noise, resource statistics, and added-binary parameter wording
beyond the Stage 26 5-run/5-seed matrix. It does not upgrade novelty,
theorem-level citation, non-binary, all-parameter, or hardware-counter claims.
```

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

Status:

```text
Stage 37 was executed through scripts/run_stage37_native_perf_counter_audit.sh
with STAGE37_RUN_BENCH=1, which requests the Stage 28 heavy counter gate.
The current WSL2 environment still has no perf command in PATH, so the gate is
BLOCKED before hardware counters or the heavy SAB benchmark can run. The
external evidence intake therefore remains missing for
stage28_native_perf_summary, and final audit A8/A8b/A9 remain
BLOCKED_EXTERNAL, MISSING_OPTIONAL_EXTERNAL_EVIDENCE, and
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED.

This is a reproducible platform blocker, not a MAT-AVX512 kernel failure.
Rerun the same Stage 37 command on native Linux or perf-enabled WSL to collect
hardware-counter evidence.
```

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

Status:

```text
Stage 38 was executed through scripts/run_stage38_fulltext_review_gate.sh with
no FAB686_FULLTEXT_PATH supplied. The artifact gate reports
BLOCKED_FULLTEXT_MISSING and creates a manual review checklist for protocol
stages, complexity, correctness/noise, parameter security, PVW-SAB delta, and
novelty boundary. Every checklist row remains blocked until a concrete
full-text source anchor is supplied.

External evidence intake still reports fab686_fulltext=MISSING, so final audit
A8b remains MISSING_OPTIONAL_EXTERNAL_EVIDENCE and A9 remains
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED.
```

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

Status:

```text
Stage 39 optional-variant triage completed. No new variant is promoted under
current evidence:

- non-binary PVW-SAB is blocked by explicit binary-only support and missing
  2025/686 full-text review;
- deeper schedule fusion is deferred because Stage 23 was neutral;
- MAT r=4 layout and additional AVX512 specialization are blocked by missing
  native hardware counters or require isolated reversible experiments;
- direct post-processing remains deferred because Stage 24 measured max tail
  at 1.261195%, below the 2.0% threshold.

The promoted active-buffer MAT-SAB path remains the current implementation
target. New code work should start only after an explicit prerequisite or new
profile changes this triage.
```

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

Status:

```text
Stage 40 scoped freeze completed. The generated decision is
SCOPED_FREEZE_READY_STRONGER_CLAIMS_BLOCKED. Required scoped artifacts exist
with SHA-256 hashes in the freeze manifest, final audit A9 remains
scoped-ready/stronger-blocked, Stage 39 promotes no new variant under current
evidence, and Stage 35 preserves the external blockers.

The post-freeze verifier then ran from a clean worktree input commit and
reported PASS_POSTFREEZE_VERIFY without regenerating the freeze package. This
checks Stage 40 decision, final audit A9, Stage 39 triage, external blockers,
manifest paths, manifest SHA-256 hashes, and the Stage 40 run-log row.

This freezes the current engineering package only. It is not a freeze for
theoretical MAT-AVX512 optimality, theorem-level 2025/686 citations, novelty,
non-binary support, or all-parameter generality.
```

## Stage 41: External Unlock Packet

Goal:

```text
Turn the remaining external blockers into executable, auditable gates so the
project can continue from the scoped engineering freeze when full-text or
native perf evidence becomes available.
```

Tasks:

- generate a machine-readable unlock matrix from final audit, blocker matrix,
  external evidence intake, Stage 37, and Stage 38;
- define exact commands for 2025/686 full-text intake, native perf-counter
  intake, external evidence registration, and final recheck;
- preserve the rule that registration is not a claim upgrade;
- keep scalar SAB and the promoted `sab_pvw_*` path unchanged.

Gate:

- every unlock row must identify current status, required evidence, command,
  manual review gate, and claim policy;
- full-text and native perf claims remain blocked while their external rows are
  missing;
- final audit A9 cannot move beyond scoped-ready until A8/A8b have direct
  evidence and manual interpretation.

Status:

```text
Stage 41 external-unlock packet generated. Current readiness remains
WAIT_EXTERNAL_FULLTEXT, WAIT_NATIVE_PERF, WAIT_EXTERNAL_ARTIFACTS, and
WAIT_UNLOCKS. This is not a new SAB optimization claim; it is the formal
continuation path for stronger paper/theory claims after external evidence is
supplied.
```

## Stage 42: Evidence Closure Audit

Goal:

```text
Machine-check that the Stage 19-44 scoped PVW/MAT-SAB evidence chain is
internally consistent after the scoped freeze and external-unlock packet.
```

Tasks:

- verify roadmap coverage for Stage 19-44;
- verify final audit scoped/pass/blocker statuses;
- verify Stage 41 external-unlock readiness remains waiting for full text and
  native perf evidence;
- verify Stage 43 current smoke summary has PASS rows for scalar binary, PVW
  target, and scalar ternary build;
- verify Stage 44 external re-probe summary preserves the current
  full-text/native-perf external-lock state;
- generate and verify a SHA-256 manifest for stable post-freeze control-plane
  artifacts;
- add and run a no-regenerate Stage 42 closure verifier from a clean worktree
  input;
- verify Stage 40 freeze manifest SHA-256 hashes still match current artifacts;
- verify run-log coverage and required control-plane files;
- preserve claim guardrails rather than upgrading blocked claims.
- expose the closure audit through `scripts/run_final_goal_recheck.sh` so it
  can be refreshed by the unified recheck entry point.

Gate:

- `S42-OVERALL` must be
  `PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED`;
- `stage42_verify_decision` must be
  `PASS_STAGE42_VERIFY_STRONGER_CLAIMS_BLOCKED` when the read-only verifier is
  used as closure-package evidence;
- any failed row means the evidence chain is not closed and must be repaired
  before relying on the final package;
- Stage 42 cannot be used as performance, novelty, or theoretical optimality
  evidence.

Status:

```text
Stage 42 evidence-closure audit generated and passed. It verifies roadmap
coverage, final-audit status labels, Stage 41 readiness, Stage 40 freeze
hashes, Stage 43 current smoke, Stage 44 external re-probe, post-freeze
verification, run-log coverage, required files, artifact-manifest entries,
post-freeze control-plane hashes, and claim guardrails. The overall result is
scoped evidence closure with stronger claims still blocked.
The audit is also integrated into the final recheck runner and passed in both
a closure-only recheck output directory and the ordinary default recheck path.
The read-only closure verifier also passed from a clean `de85276` input commit:
it confirmed final audit A9, Stage 41 waiting readiness, Stage 42 closure,
Stage 43 current smoke, default and closure-only final recheck closure,
required Stage 42/43 run-log rows, artifact-manifest registration, and closure
manifest hashes without regenerating the audit.
```

## Stage 43: Post-Closure Current Smoke

Goal:

```text
Refresh current-head scalar/PVW build and correctness smoke evidence after the
Stage 42 evidence-closure audit.
```

Tasks:

- rerun the Stage 33 smoke runner with an isolated Stage 43 output directory;
- verify scalar binary `SET_2_3_2048` full run ends with `Pass`;
- verify explicit PVW target full bootstrap gate reports `Pass`;
- verify scalar ternary build still passes independently of the binary PVW
  path;
- keep this evidence scoped to current-state correctness/build health only.

Gate:

- all three smoke rows in
  `repro/stage43_current_smoke_after_stage42/summary.csv` must be `PASS`;
- this stage cannot be used as a performance, novelty, or theoretical
  optimality result.

Status:

```text
Stage 43 current-head smoke passed on WSL/Linux with `spqlios_avx512`.
Scalar binary full run, explicit PVW target full gate, and scalar ternary build
all passed. The result refreshes current-state smoke evidence after the
closure audit while preserving the stronger-claims-blocked boundary.
```

## Stage 44: External Unlock Re-probe

Goal:

```text
Refresh the two remaining external unlock checks after the Stage 42/43 closure
package: 2025/686 full-text availability and native/perf hardware-counter
availability.
```

Tasks:

- rerun the 2025/686 citation/full-text access probe in an isolated Stage 44
  output directory;
- rerun the Stage 28 native perf gate in an isolated Stage 44 output directory;
- register supplied external artifacts if `FAB686_FULLTEXT_PATH` or
  `STAGE28_NATIVE_PERF_SUMMARY` is provided;
- summarize whether the project can proceed to manual full-paper review or
  MAT-AVX512 hardware-counter interpretation;
- keep all claims scoped unless an external artifact is available and manually
  reviewed.

Gate:

- `citation_probe_command` must be `PASS`;
- `stage44_decision` remains `WAIT_EXTERNAL_UNLOCKS` under the current
  environment;
- if `stage44_decision` becomes
  `READY_FOR_MANUAL_REVIEW_OR_PERF_INTERPRETATION`, no claim is upgraded until
  the relevant manual review is completed and the final audit is updated.

Status:

```text
Stage 44 external-unlock re-probe completed. The citation probe ran, but direct
full-text access remains blocked and no open-access PDF was reported. The
native perf gate also remains blocked in the current WSL2 environment because
hardware-counter evidence is not available. The stage decision is
WAIT_EXTERNAL_UNLOCKS, so the scoped engineering claim remains the strongest
completed result.

The Stage 44 re-probe is now also callable from the unified final recheck
runner with `FINAL_RECHECK_STAGE44_REPROBE=1`. The isolated
`repro/final_goal_recheck_stage44_reprobe/summary.csv` run passed
`stage44_external_reprobe`, rebuilt the final audit, refreshed Stage 42
closure, and preserved
`SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`.
```

## Stage 45: Active-State Refactor Maintenance

Goal:

```text
Keep the promoted Stage 20 active-buffer/copyback fusion implementation
maintainable by making the internal PVW accumulator ping-pong state explicit,
without changing scalar SAB, the public sab_pvw_* API, or any performance
claim.
```

Tasks:

- introduce an internal accumulator state structure carrying the two PVW
  buffers, active buffer index, lane count, `in_N`, and `r_prec`;
- route the active-buffer sparse path through this state instead of raw local
  pointer/parity variables;
- preserve public API normalization for `sab_pvw_RGSW_monomial_mul()`;
- record a portable correctness gate and any current-platform AVX512 build
  limitation in the repro pack;
- add Stage45 to closure/manifest/verifier checks so post-closure code changes
  remain auditable.

Gate:

- `SAB_PVW_KERNEL_TEST=true` with `SAB_PVW_ACTIVE_BUFFER_FUSION=true` must pass
  r=1/2/4 sparse_mul and full bootstrap lane equivalence;
- Windows/MSYS `spqlios_avx512` failures may only be recorded as platform
  limitations, not as performance or algorithmic evidence;
- Stage42 closure must include `S42-STAGE45-ACTIVE-STATE=PASS` before relying
  on the post-closure code state.

Status:

```text
Stage 45 added `SAB_PVW_Accumulator_State` inside `src/sab_pvw.c`. The public
PVW API and scalar SAB path remain unchanged. The portable FFNT active-state
kernel gate passed for r=1/2/4 sparse_mul and full bootstrap lane equivalence.
The current Windows/MSYS `spqlios_avx512` build remains blocked by assembler
`.seh_savexmm` errors, so no AVX512 correctness or performance conclusion is
drawn from that platform. The Stage42 closure audit now checks the Stage45
summary and keeps the final decision scoped-ready with stronger claims blocked.
```

## Stage 46: WSL Active-State Target Smoke

Goal:

```text
Refresh target-shape PVW/MAT-SAB correctness on the selected WSL/Linux
performance platform after the Stage 45 active-state refactor.
```

Tasks:

- run the explicit PVW target full bootstrap gate on WSL/Linux with
  `spqlios_avx512`;
- keep the promoted explicit path flags enabled:
  `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true` and
  `SAB_PVW_ACTIVE_BUFFER_FUSION=true`;
- record raw build/run logs and a machine-readable summary;
- keep the result scoped to correctness/build health, not latency or
  hardware-counter attribution.

Gate:

- `SAB_PVW target full bootstrap gate: Pass` must appear in the WSL run log;
- the Stage46 summary row must be `PASS`;
- Stage42 closure/verifier must include the Stage46 artifact before relying on
  current-head post-refactor target correctness.

Status:

```text
Stage 46 WSL/Linux target smoke passed under `spqlios_avx512`, specialized
MAT-AVX512, and active-buffer fusion. The run confirmed target full bootstrap
lane equivalence for r=2, h=39, r_prec=7 on `BINARY SET_2_3_2048`. This
refreshes current-head correctness evidence after the active-state refactor
but does not add a new performance claim.
```

## Stage 47: WSL Full-SAB Current-Head Smoke

Goal:

```text
Refresh complete SAB A/B smoke evidence on WSL/Linux after the active-state
refactor, while keeping Stage 36 as the statistical performance evidence.
```

Tasks:

- run `scripts/run_stage20_active_buffer_bench.sh` at current head for r=2 and
  r=4;
- keep `spqlios_avx512`, specialized MAT-AVX512, and active-buffer fusion
  enabled;
- record one-run complete-SAB A/B summaries and raw run logs;
- report the result as smoke-only, not as a new high-stat performance claim.

Gate:

- each run must print `SAB_PVW_BENCH correctness target_full ... Pass`;
- r=2 and r=4 summary rows must be `PASS`;
- speedup must remain positive for the smoke to support current-head
  continuity;
- Stage42 closure/verifier must include Stage47 before relying on this
  current-head full-SAB smoke.

Status:

```text
Stage 47 WSL/Linux complete-SAB smoke passed. r=2 reached 1.212x in one
process run and r=4 reached 1.353x in one process run under `spqlios_avx512`,
specialized MAT-AVX512, and active-buffer fusion. This preserves current-head
continuity after the active-state refactor; Stage 36 remains the high-stat
performance evidence for claims.
```

## Stage 48: WSL Final-Output Noise Smoke

Goal:

```text
Refresh current-head final-output noise and correctness smoke evidence on
WSL/Linux after the active-state refactor and the Stage 47 complete-SAB A/B
smoke, while keeping Stage 36 as the high-stat noise evidence.
```

Tasks:

- run `scripts/run_stage25_final_noise_sweep.sh` at current head for r=2 and
  r=4;
- keep `spqlios_avx512`, specialized MAT-AVX512, and active-buffer fusion
  enabled;
- record one seed with `SAB_PVW_NOISE_TRIALS=1` as current-head continuity
  evidence;
- report the result as smoke-only, not as a replacement for the Stage 36
  50-seed target-noise campaign.

Gate:

- each r must produce a `PASS` aggregate row;
- `pvw_failures`, `scalar_failures`, and `pair_failures` must be zero for
  r=2 and r=4;
- Stage42 closure/verifier must include Stage48 before relying on this
  current-head noise smoke.

Status:

```text
Stage 48 WSL/Linux final-output noise smoke passed. r=2 covered 4096 points
with zero PVW/scalar/pair failures and pvw_minus_scalar_log2=0.603. r=4
covered 8192 points with zero PVW/scalar/pair failures and
pvw_minus_scalar_log2=-0.555. This preserves current-head noise continuity
after the active-state refactor; Stage 36 remains the high-stat noise evidence
for claims.
```

## Stage 49: WSL Repeated Full-SAB Current-Head Stability

Goal:

```text
Strengthen the post-refactor current-head complete-SAB A/B evidence from
single-run smoke to a repeated stability check, while keeping Stage 36 as the
high-stat performance claim source.
```

Tasks:

- run `scripts/run_stage20_active_buffer_bench.sh` at current head for r=2 and
  r=4;
- use 3 process runs and 1 paired timing rep per process;
- keep `spqlios_avx512`, specialized MAT-AVX512, and active-buffer fusion
  enabled;
- record per-run raw logs, per-r summaries, and an aggregate summary;
- label the result as current-head repeated stability evidence, not as a
  replacement for Stage 36 high-stat performance.

Gate:

- all six process runs must print
  `SAB_PVW_BENCH correctness target_full ... Pass`;
- r=2 and r=4 aggregate rows must be `PASS`;
- each r must have `runs=3`;
- `speedup_min` must remain above 1.0 for both r values;
- Stage42 closure/verifier must include Stage49 before relying on this
  current-head repeated full-SAB stability check.

Status:

```text
Stage 49 WSL/Linux repeated complete-SAB current-head check passed. r=2 had
mean speedup 1.265x over 3 runs, with range 1.174x-1.338x. r=4 had mean
speedup 1.376x over 3 runs, with range 1.356x-1.396x. This strengthens
post-refactor current-head continuity for the promoted explicit path; Stage 36
remains the high-stat performance evidence for claims.
```

## Stage 50: Performance Evidence Matrix

Goal:

```text
Unify Stage 36 high-stat target performance, Stage 47 current-head smoke, and
Stage 49 current-head repeated stability into a single claim-boundary matrix
so performance wording cannot confuse smoke, stability, and high-stat evidence.
```

Tasks:

- generate `repro/stage50_performance_evidence_matrix.csv`;
- generate `docs/stage50_performance_evidence_matrix.md`;
- verify r=2/r=4 Stage 36 rows remain 10-run target-performance references;
- verify r=2/r=4 Stage 49 rows remain current-head repeated stability only;
- verify Stage47 is explicitly marked single-run smoke and superseded by
  Stage49 for current-head continuity wording;
- preserve stronger-claim blockers for novelty, theorem-level 2025/686,
  native hardware-counter attribution, non-binary, and all-parameter claims.

Gate:

- all matrix rows must be `PASS`;
- Stage36 r=2/r=4 CI95 lower bounds must remain above 1.0;
- Stage49 r=2/r=4 mean speedups must remain within the Stage36 CI95 band;
- stats/claim labels must distinguish high-stat target performance from
  current-head stability and single-run smoke;
- Stage42 closure/verifier must include Stage50 before relying on the updated
  performance evidence boundary.

Status:

```text
Stage 50 passed. Stage36 remains the performance claim source: r=2 mean
1.191x with CI95 [1.075307, 1.306693], and r=4 mean 1.377x with CI95
[1.314893, 1.438107]. Stage49 current-head repeated stability is consistent
with Stage36: r=2 mean 1.265x and r=4 mean 1.376x both fall within the
corresponding Stage36 CI95 bands. Stage47 is retained as historical one-run
smoke and is superseded by Stage49 for current-head continuity wording.
Stronger claims remain blocked.
```

## Stage 51: Goal Completion Frontier

Goal:

```text
Convert the current Stage19+ evidence state into an auditable frontier:
which parts of the original PVW/MAT-SAB acceleration goal are locally ready,
which parts remain scoped-only, and which stronger claims still require
external evidence or manual review.
```

Tasks:

- generate `repro/stage51_goal_completion_frontier.csv`;
- generate `docs/stage51_goal_completion_frontier.md`;
- read authoritative status from the final audit, Stage42 closure, Stage50
  performance matrix, and remaining blocker dashboard;
- classify local engineering/performance/noise/resource/reproducibility lanes;
- preserve external blockers for native perf attribution, novelty review, and
  2025/686 full-text theorem/protocol review;
- explicitly keep the active goal open unless external blockers are resolved
  or the user narrows the goal scope.

Gate:

- G1-G6 local lanes must be `LOCAL_READY` or `LOCAL_SCOPED_READY`;
- B1-B3 blocker lanes must remain blocked unless concrete external evidence is
  registered;
- G9 must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- Stage42 closure/verifier must include Stage51 before relying on the frontier.

Status:

```text
Stage 51 passed with `PASS_GOAL_FRONTIER_SCOPED_READY_STRONGER_BLOCKED`.
The scoped engineering chain is locally ready for target binary PVW/MAT-SAB
acceleration evidence. The active goal remains open because MAT-AVX512 native
perf attribution, novelty/full related-work review, and 2025/686 full-text
theorem/protocol citation review remain externally blocked.
```

## Stage 52: External-Unlock Readiness Packet

Goal:

```text
Turn the remaining external blockers into an exact input/command/artifact/gate
packet so native perf, 2025/686 full-text, novelty review, external
registration, and final recheck can be executed reproducibly when the missing
external inputs become available.
```

Tasks:

- generate `repro/stage52_external_unlock_readiness.csv`;
- generate `docs/stage52_external_unlock_readiness.md`;
- derive rows from Stage41 external unlock packet, Stage51 frontier, and the
  remaining blocker dashboard;
- record required inputs, commands, expected artifacts, acceptance gates, and
  failure policies for CB5, CB6, CB7, A8/A8b, and A9;
- preserve the rule that external artifact registration alone does not upgrade
  paper/theory claims.

Gate:

- native perf row must remain `WAIT_NATIVE_PERF` with a Stage28 command and
  hardware-counter acceptance gate;
- 2025/686 full-text row must remain `WAIT_EXTERNAL_FULLTEXT` with a Stage38
  command and hash/recognized-source acceptance gate;
- novelty row must remain `WAIT_MANUAL_FULLTEXT_REVIEW`;
- final recheck row must remain `WAIT_UNLOCKS`;
- Stage42 closure/verifier must include Stage52 before relying on the unlock
  readiness packet.

Status:

```text
Stage 52 passed with `PASS_EXTERNAL_UNLOCK_READINESS_PACKET`. The packet fixes
the exact commands and artifacts needed to unlock stronger claims, while
preserving the current scoped-ready/stronger-blocked decision.
```

## Stage 53: Final-Recheck Integration for Stage 50-52

Goal:

```text
Make the unified final recheck regenerate Stage50 performance evidence matrix,
Stage51 goal frontier, and Stage52 external-unlock readiness before rebuilding
Stage42 closure, so the latest claim-boundary artifacts cannot silently go
stale.
```

Tasks:

- extend `scripts/run_final_goal_recheck.sh` with optional
  `FINAL_RECHECK_STAGE50_MATRIX`, `FINAL_RECHECK_STAGE51_FRONTIER`, and
  `FINAL_RECHECK_STAGE52_UNLOCK_READINESS` switches;
- preserve the existing postfreeze-only no-write verifier behavior;
- run an isolated local final recheck with heavy/network/external probes
  disabled and Stage50-52 enabled;
- record summary and raw logs under `repro/stage53_final_recheck_stage50_52`;
- keep the final decision scoped-ready with stronger claims blocked.

Gate:

- Stage50, Stage51, and Stage52 recheck steps must pass;
- Stage42 closure must pass after those steps;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- no heavy benchmark, network, native perf, or full-text claim upgrade is
  implied by this integration step.

Status:

```text
Stage 53 passed. The isolated final recheck regenerated Stage50, Stage51, and
Stage52 artifacts, rebuilt Stage42 closure, and preserved
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED.
```

## Stage 54: Default Final-Recheck Coverage

Goal:

```text
Verify that the default final recheck path now regenerates Stage50, Stage51,
Stage52, and Stage42 closure without requiring explicit Stage50-52 switches.
```

Tasks:

- run `scripts/run_final_goal_recheck.sh` with only
  `FINAL_RECHECK_OUT_DIR=repro/stage54_default_final_recheck`;
- record default summary and raw logs;
- verify Stage50, Stage51, Stage52, and Stage42 closure pass under default
  final recheck behavior;
- keep final decision scoped-ready with stronger claims blocked.

Gate:

- default final recheck must pass Stage50, Stage51, Stage52, and Stage42
  closure steps;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- Stage42 closure/verifier must include Stage54 before relying on default
  final recheck coverage.

Status:

```text
Stage 54 passed. The default final recheck ran Stage50, Stage51, Stage52, and
Stage42 closure, and preserved
SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED.
```

## Stage 55: External Paper Metadata and Full-Text Probe

Goal:

```text
Strengthen the remaining 2025/686 full-text blocker evidence by recording
official DOI/Crossref metadata, full-text route availability, Cloudflare/403
blocking, and the exact claim policy for theorem-level review.
```

Tasks:

- probe the official IACR ePrint PDF/page and ACM DOI PDF/page routes;
- probe the author publication page and public implementation repository;
- fetch and store Crossref DOI metadata for `10.1145/3719027.3765181`;
- distinguish metadata availability from recognized full-text availability;
- keep theorem, algorithm, table, figure, and experiment-number claims blocked
  unless a recognized full-text artifact is registered and manually reviewed;
- add Stage55 artifacts to the Stage42 closure audit so the blocker state is
  machine-checkable.

Gate:

- Crossref DOI metadata must be `PASS`;
- official full-text routes must either report `PDF_ACCESSIBLE` or a recorded
  blocked status such as `BLOCKED_CLOUDFLARE_CHALLENGE`/`BLOCKED_403`;
- `stage55_decision` must be either
  `FULLTEXT_AVAILABLE_REVIEW_REQUIRED` or
  `WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW`;
- if no full text is available, the stronger-claim blockers remain active.

Status:

```text
Stage55 passed and remains part of the Stage19-71 control-plane closure. It
does not change scalar SAB, `sab_pvw_*`, performance evidence, or the scoped
engineering claim. Its output only improves the auditability of the external
2025/686 full-text blocker and the next manual-review gate.
```

## Stage 56: Stage55 Final-Recheck Integration

Goal:

```text
Make Stage55 refreshable through the unified final recheck runner before
blocker/frontier/unlock/closure artifacts are regenerated.
```

Tasks:

- add `FINAL_RECHECK_STAGE55_PAPER_PROBE=1` to
  `scripts/run_final_goal_recheck.sh`;
- keep the default final recheck lightweight by not running the network paper
  probe unless the flag is explicitly enabled;
- run an isolated final recheck that refreshes Stage55, remaining blockers,
  Stage51, Stage52, and Stage42 closure;
- register the Stage56 summary and raw logs in the repro pack;
- add Stage56 to Stage42 closure and verifier checks.

Gate:

- `stage55_external_paper_probe` must be `PASS`;
- remaining blocker dashboard, Stage51 frontier, Stage52 unlock readiness, and
  Stage42 closure must all be `PASS`;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- no performance, novelty, or theorem-level claim is upgraded by this stage.

Status:

```text
Stage 56 passed. The explicit Stage55 final-recheck path regenerated the
external paper probe and propagated its still-blocked full-text status through
the remaining blocker dashboard, Stage51 frontier, Stage52 unlock readiness,
and Stage42 closure. Stronger claims remain blocked.
```

## Stage 57: Scope Label Consistency Audit

Goal:

```text
Prevent current control-plane reports from citing stale Stage19+ closure
ranges after later stages extend the evidence chain.
```

Tasks:

- make Stage51 derive the latest closure range from the roadmap instead of a
  hard-coded Stage19 range;
- scan current scope/control files for stale `Stage 19-44`, `Stage19-44`,
  `Stage 19-50`, or `Stage19-50` labels;
- verify Stage42 overall, Stage51 G6, and current scope files all point to the
  latest roadmap range;
- record the audit in the repro pack and Stage42 closure/verifier.

Gate:

- roadmap latest stage must be at least the current stage;
- Stage42 overall must mention the latest `Stage 19-*` range;
- Stage51 G6 must mention the latest `Stage19-*` range;
- current scope files must not contain stale Stage19-44/50 labels.

Status:

```text
Stage 57 passed. Stage51 now emits the current closure range dynamically, and
the scope-label audit confirms that current control files refer to the latest
Stage19+ closure range while preserving stronger-claim blockers.
```

## Stage 58: Stage57 Final-Recheck Integration

Goal:

```text
Make the Stage57 scope-label audit refresh automatically in the unified final
recheck before Stage42 closure is rebuilt.
```

Tasks:

- add `FINAL_RECHECK_STAGE57_SCOPE_LABEL_AUDIT` to
  `scripts/run_final_goal_recheck.sh`;
- run Stage57 after Stage51 frontier and Stage52 unlock readiness are
  regenerated, and before Stage42 closure;
- keep the post-freeze no-write verifier mode narrow when Stage57 is disabled;
- record an isolated Stage58 final recheck output and raw logs;
- add Stage58 to Stage42 closure/verifier checks.

Gate:

- `stage57_scope_label_audit` must be `PASS`;
- Stage51 frontier, Stage52 unlock readiness, and Stage42 closure must be
  `PASS`;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- this stage must not upgrade performance, novelty, theorem-level, or
  hardware-counter claims.

Status:

```text
Stage 58 passed. The unified final recheck can now refresh Stage57 before
Stage42 closure and preserves
`SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`.
```

## Stage 59: Completion Route Readiness

Goal:

```text
Convert the post-Stage58 state into an explicit, machine-checkable route to
completion so Codex can keep moving without silently narrowing the original
PVW/MAT-SAB acceleration goal.
```

Tasks:

- add `docs/roadmap_to_completion_after_stage58.md` as the forward route for
  Stage60+ work;
- generate `repro/stage59_completion_route_readiness.csv` from Stage50,
  Stage51, Stage52, and the remaining blocker dashboard;
- generate `docs/stage59_completion_route_readiness.md`;
- separate local-refresh lanes from external native-perf, full-text, novelty,
  and final-freeze lanes;
- add Stage59 to Stage42 closure/verifier checks.

Gate:

- local scoped engineering evidence must remain `LOCAL_READY`;
- current-head refresh must be `READY_LOCAL_REFRESH`;
- native perf, 2025/686 full text, and novelty review lanes must remain
  explicitly blocked unless their external gates are actually satisfied;
- final route decision must be
  `PASS_COMPLETION_ROUTE_READY__STRONGER_CLAIMS_BLOCKED`;
- no performance, theorem-level, novelty, or hardware-counter claim is
  upgraded by this route-codification stage.

Status:

```text
Stage 59 passed. It codifies the route from the scoped engineering closure to
eventual stronger-claim completion while preserving the current blocker
boundary.
```

## Stage 60: Stage59 Final-Recheck Integration

Goal:

```text
Make the Stage59 completion-route readiness table refresh automatically in the
unified final recheck before Stage42 closure is rebuilt.
```

Tasks:

- add `FINAL_RECHECK_STAGE59_COMPLETION_ROUTE` to
  `scripts/run_final_goal_recheck.sh`;
- run Stage59 after Stage51 frontier, Stage52 unlock readiness, and Stage57
  scope-label audit are refreshed, and before Stage42 closure;
- keep the post-freeze no-write verifier mode narrow when Stage59 is disabled;
- record an isolated Stage60 final recheck output and raw logs;
- add Stage60 to Stage42 closure/verifier checks.

Gate:

- `stage59_completion_route` must be `PASS`;
- Stage51 frontier, Stage52 unlock readiness, Stage57 scope-label audit, and
  Stage42 closure must be `PASS`;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- this stage must not upgrade performance, novelty, theorem-level, or
  hardware-counter claims.

Status:

```text
Stage 60 passed. The unified final recheck can now refresh Stage59 route
readiness before Stage42 closure and preserves
`SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`.
```

## Stage 61: Native Perf Unlock Probe

Goal:

```text
Rerun the native perf-counter unlock command from Stage52 and determine whether
the current platform can unlock MAT-AVX512 hardware-counter attribution.
```

Tasks:

- run `scripts/run_stage28_native_perf_counter_gate.sh` with
  `STAGE28_RUN_BENCH=1` into `repro/stage61_native_perf_unlock_probe`;
- record platform metadata, perf command availability, and the
  `hardware_counter_gate` decision;
- add Stage61 to Stage42 closure/verifier checks;
- preserve CB5/A8 as blocked unless `hardware_counter_gate=PASS` and
  `bench_correctness=PASS`.

Gate:

- if `perf` is missing or counters are unusable, Stage61 must be recorded as a
  blocked unlock probe and must not upgrade MAT-AVX512 theory claims;
- if `hardware_counter_gate=PASS`, the raw counter logs and correctness row
  must be reviewed before any load/store/FMA attribution wording is promoted;
- scalar SAB and `sab_pvw_*` code paths are not modified by this stage.

Status:

```text
Stage 61 ran on the current WSL2 platform. `perf` is missing, so
`hardware_counter_gate=BLOCKED`; MAT-AVX512 theoretical load/store/FMA
attribution remains externally blocked.
```

## Stage 62: 2025/686 Full-Text Unlock Probe

Goal:

```text
Rerun the 2025/686 full-text unlock gate and determine whether theorem-level
protocol citation, complexity, noise/security, and novelty review can start.
```

Tasks:

- probe official ACM DOI PDF and IACR ePrint PDF direct routes and record
  access status;
- run the Stage38 full-text artifact gate into
  `repro/stage62_fulltext_unlock_probe`;
- regenerate external evidence intake with the current environment;
- produce `repro/stage62_fulltext_unlock_probe/unlock_summary.csv` and
  `docs/stage62_fulltext_unlock_probe_log.md`;
- add Stage62 to Stage42 closure/verifier checks.

Gate:

- if no recognized `FAB686_FULLTEXT_PATH` artifact is supplied, Stage62 must
  stay in `WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW`;
- direct-route 403/Cloudflare blocks are recorded evidence, not an unlock;
- theorem-level, algorithm/table/figure/experiment-number, and novelty claims
  remain blocked until a full-text artifact is registered and manually mapped
  to source anchors.

Status:

```text
Stage 62 ran on the current WSL2/network path. ACM DOI PDF and IACR ePrint PDF
direct routes are blocked by Cloudflare/403 challenge, and no local
`FAB686_FULLTEXT_PATH` artifact is registered. Stage62 remains
WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW.
```

## Stage 64A: Post-Variant Implementation Refresh

Goal:

```text
After the Stage65A code change, refresh current-head evidence for the default
promoted active-buffer PVW/MAT-SAB path and scalar SAB baseline.
```

Tasks:

- run scalar binary, PVW target, and scalar ternary current smoke;
- run r=2/r=4 complete-SAB repeated A/B with three process runs per r;
- run r=2/r=4 final-output noise smoke;
- confirm Stage50 performance evidence matrix still passes;
- keep Stage65A negative and not promoted.

Gate:

- scalar binary smoke, PVW target gate, and scalar ternary build must pass;
- r=2/r=4 repeated full-SAB runs must pass correctness and have speedup_min > 1;
- r=2/r=4 final-output noise smoke must have zero PVW/scalar/pair failures;
- Stage50 matrix must pass; this remains continuity evidence, not a new
  high-stat claim.

Status:

```text
Stage64A passed after the Stage65A code change. r=2 complete-SAB speedup mean
was 1.269x with min 1.247x. r=4 mean was 1.445x with min 1.352x. Final-output
noise smoke passed for r=2/r=4 with zero failures, and Stage50 remained PASS.
```

## Stage 65A: R4 Row-Unrolled AVX512 Optional Variant

Goal:

```text
Evaluate a reversible r=4 MAT external-product implementation variant without
changing scalar SAB, the default promoted PVW path, or the MAT_TRGSW key layout.
```

Tasks:

- add explicit compile flag `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS`;
- implement a `k=1,l=1,r=4` AVX512 row-unrolled MAT external-product variant;
- compare it against the current specialized MAT-AVX512 baseline under the
  same `spqlios_avx512` backend;
- record staged kernel, complete-SAB smoke, objdump proxy, and default scalar
  baseline smoke evidence.

Gate:

- correctness must pass for both specialized and r4-unrolled variants;
- any positive kernel result must still pass complete-SAB A/B before promotion;
- one-run smoke cannot upgrade the promoted path;
- scalar SAB default behavior must remain buildable and runnable.

Status:

```text
Stage65A ran on WSL/Linux. The r4 row-unrolled AVX512 variant preserved
correctness, but was negative versus the specialized baseline: dft-output MAT
ratio 0.930815x, full-output MAT ratio 0.986900x, and one-run complete-SAB r=4
PVW latency ratio 0.803554x. Objdump proxy counts were unchanged. The variant
is retained as a negative ablation and is not promoted.
```

## Stage 66A: Post-Variant Final-Recheck Integration

Goal:

```text
After Stage65A and Stage64A, verify that the lightweight final-recheck control
plane can refresh the post-variant evidence state and preserve the scoped-ready
/ stronger-blocked claim boundary.
```

Tasks:

- run the final recheck with network citation probes, related-work probes,
  native `perf`, current smoke, Stage44 re-probe, and Stage55 paper probe
  disabled;
- regenerate the Stage27 final package, external evidence intake,
  conditional backlog, final audit, remaining blocker dashboard, Stage50,
  Stage51, Stage52, Stage57, and Stage59;
- intentionally skip Stage42 closure inside the recheck, then rebuild Stage42
  closure after the Stage66A summary exists;
- record Stage64A as still passed and Stage65A as still negative/not promoted.

Gate:

- Stage66A final-recheck core must pass;
- Stage64A continuity must remain `PASS_POST_VARIANT_REFRESH`;
- Stage65A must remain `NEGATIVE_NOT_PROMOTED`;
- Stage42 closure and verifier must register Stage66A before relying on the
  updated post-variant control plane.

Status:

```text
Stage66A passed. It refreshes the lightweight post-variant final-recheck
control plane while preserving Stage64A continuity and the Stage65A negative
variant decision. It does not modify scalar SAB, sab_pvw_*, MAT kernels,
parameters, or benchmarks.
```

## Stage 67: Final-Recheck Stage66A Integration

Goal:

```text
Make scripts/run_final_goal_recheck.sh able to run Stage66A through an
explicit FINAL_RECHECK_STAGE66_POST_VARIANT=1 switch, then rebuild Stage42
closure after the Stage67 summary is finalized.
```

Tasks:

- add a non-recursive Stage66A switch to the unified final recheck runner;
- run an isolated final recheck with Stage66A enabled and Stage42 closure
  intentionally skipped inside that run;
- build a Stage67 decision log from the final recheck summary and canonical
  Stage66A summary;
- register Stage67 in Stage42 closure, the read-only verifier, run log,
  artifact manifest, and reproduction checklist.

Gate:

- `stage66_post_variant_final_recheck` must pass inside the Stage67 final
  recheck;
- `stage42_evidence_closure` must be skipped inside the Stage67 final recheck
  and pass in the post-summary rebuild;
- `final_decision` must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- canonical Stage66A must remain `PASS_POST_VARIANT_FINAL_RECHECK`.

Status:

```text
Stage67 passed. The unified final recheck can now refresh Stage66A through an
explicit non-recursive switch, then Stage42 closure can be rebuilt after the
Stage67 summary is finalized. This does not run a new SAB benchmark and cannot
upgrade speedup, novelty, theorem-level, non-binary, all-parameter, or native
hardware-counter claims.
```

## Stage 68: Frontier Closure Consistency

Goal:

```text
Repair and verify the post-Stage67 control-plane consistency between Stage42
closure, Stage51 goal frontier, Stage57 scope-label audit, and Stage59
completion route.
```

Tasks:

- make Stage42 overall emit the latest Stage19+ control-plane label;
- regenerate Stage51, Stage57, and Stage59 after that label is visible;
- add a Stage68 audit that checks Stage42, Stage51 G6, Stage57, and Stage59
  agree on the latest control-plane label and local-ready status;
- register Stage68 in Stage42 closure and the read-only verifier.

Gate:

- Stage42 `S42-OVERALL` must pass and mention the latest Stage19+ label;
- Stage51 `G6` must be `LOCAL_READY`;
- Stage57 scope-label audit must pass;
- Stage59 current-head refresh route must include Stage67 evidence;
- Stage68 decision must be `PASS_FRONTIER_CLOSURE_CONSISTENCY`.

Status:

```text
Stage68 passed and remains consistent after the Stage71 closure refresh.
Stage42, Stage51 G6, Stage57, and Stage59 agree on the latest control-plane
closure label. It did not run a new SAB benchmark and did not upgrade speedup,
novelty, theorem-level, non-binary, all-parameter, or native hardware-counter
claims.
```

## Stage 69: Local Variant Feasibility Audit

Goal:

```text
Determine whether any remaining local PVW/MAT-SAB optimization candidate is
ready for new code work after the promoted active-buffer path, the Stage65A
negative r=4 row-unrolled AVX512 variant, and the Stage68 closure repair.
```

Tasks:

- audit H2 post-processing, H3 SAB-specific sparse MAT, H4 schedule fusion,
  H7 AVX512 layout/tiling, and H8 branch generalization against the current
  evidence;
- write a theory check and candidate card for the H3 sparse-selector shortcut;
- reject/defer/block candidates that lack a safe theory, native perf evidence,
  full-text protocol support, or positive prior profile signal;
- preserve the promoted active-buffer PVW/MAT-SAB path and scalar baseline;
- register the decision in the repro pack and Stage42 closure/verifier.

Gate:

- H3 direct selector-value skipping must be rejected unless a leakage/security
  and key-format design exists;
- H2/H4/H7/H8 must not be reopened without their documented unlock evidence;
- Stage69 decision must be
  `PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED`;
- this stage must not modify SAB code or upgrade performance, theorem-level,
  novelty, non-binary, all-parameter, or native hardware-counter claims.

Status:

```text
Stage69 passed and is registered in the Stage19-71 closure. It is a routing
and theory-control step only; any future implementation change still needs a
separate Stage65-style correctness, full-SAB A/B, noise, resource, and
post-variant refresh loop.
```

## Stage 70: External Unlock Preflight

Goal:

```text
Make the remaining native-perf, 2025/686 full-text, novelty-review, and
local-variant unlock requirements machine-checkable after Stage69.
```

Tasks:

- read Stage59, Stage61, Stage62, and Stage69 evidence;
- check whether `FAB686_FULLTEXT_PATH` is set to a non-empty local file;
- record the native-perf, full-text, novelty, and local-variant next actions
  in a single preflight artifact;
- register Stage70 in the repro pack and Stage42 closure/verifier;
- preserve the scalar SAB baseline and promoted PVW/MAT-SAB path.

Gate:

- Stage70 decision must be
  `PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED`;
- if native perf is unavailable, MAT-AVX512 load/store/FMA optimality wording
  remains blocked;
- if no reviewed 2025/686 full text is registered, theorem-level and novelty
  claims remain blocked;
- if Stage69 reports no unblocked local variant, no new code work starts
  without a new falsifiable hypothesis.

Status:

```text
Stage70 passed. It records the native-perf, full-text, novelty-review, and
local-variant prerequisites needed for stronger claims after Stage69. It is an
audit and handoff step only; it cannot upgrade speedup, novelty, theorem-level,
non-binary, all-parameter, or hardware-counter claims.
```

## Stage 71: Final-Recheck Stage70 Integration

Goal:

```text
Make Stage70 external-unlock preflight refreshable through the unified final
recheck before Stage42 closure is rebuilt.
```

Tasks:

- add `FINAL_RECHECK_STAGE70_UNLOCK_PREFLIGHT` to
  `scripts/run_final_goal_recheck.sh`;
- run an isolated final recheck that refreshes Stage51, Stage52, Stage57,
  Stage59, Stage70, and Stage42 closure while skipping heavy gates;
- build a Stage71 decision log from the final recheck summary and canonical
  Stage70 preflight;
- register Stage71 in the repro pack and Stage42 closure/verifier.

Gate:

- Stage70 must pass inside the final recheck summary;
- Stage42 closure must pass after Stage70 is refreshed;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- no SAB benchmark, scalar/PVW code path, speedup, novelty, theorem-level,
  non-binary, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage71 passed. The unified final recheck can refresh Stage70 external-unlock
preflight before rebuilding Stage42 closure. It is control-plane evidence only.
```

## Stage 72: External Source Refresh

Goal:

```text
Refresh current external source availability for 2025/686 after Stage71 and
record whether metadata/code/full-text routes can support stronger claim work.
```

Tasks:

- probe official ePrint and ACM full-text routes;
- probe the author publication page and author-provided BibTeX route;
- probe Crossref DOI metadata and the author-linked GitHub implementation
  route;
- record the access matrix and claim policy in the repro pack;
- update the remaining blocker dashboard and Stage42 closure/verifier.

Gate:

- author metadata and BibTeX metadata must be available or explicitly failed;
- DOI metadata must be available or explicitly failed;
- direct ePrint/ACM PDF routes must either provide a PDF or remain recorded as
  blocked;
- `stage72_decision` must be
  `PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED`;
- no SAB benchmark, scalar/PVW code path, speedup, novelty, theorem-level,
  non-binary, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage72 passed. Author metadata, BibTeX metadata, Crossref DOI metadata, and
the author-linked implementation route are reachable, while direct ePrint/ACM
PDF routes remain blocked or unavailable as a reviewed local full-text
artifact. It is external-source evidence only.
```

## Stage 73: Final-Recheck Stage72 Integration

Goal:

```text
Make Stage72 external-source refresh available through the unified final
recheck before blocker dashboards, frontier summaries, and Stage42 closure are
rebuilt.
```

Tasks:

- add `FINAL_RECHECK_STAGE72_SOURCE_REFRESH` to
  `scripts/run_final_goal_recheck.sh`;
- run an isolated final recheck that refreshes Stage72, final audit,
  remaining blockers, Stage51, Stage52, Stage57, Stage59, Stage70, and Stage42
  closure while skipping heavy gates;
- build a Stage73 decision log from the final recheck summary and canonical
  Stage72 source-refresh summary;
- register Stage73 in the repro pack and Stage42 closure/verifier.

Gate:

- Stage72 must pass inside the final recheck summary;
- Stage42 closure must pass after Stage72 is refreshed;
- final decision must remain
  `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED`;
- heavy benchmark, citation, related-work, current-smoke, Stage55, Stage50,
  and Stage66 refreshes must remain explicitly skipped for this control-plane
  run;
- no SAB benchmark, scalar/PVW code path, speedup, novelty, theorem-level,
  non-binary, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage73 passed. The unified final recheck can refresh Stage72 external-source
availability before rebuilding blocker/frontier/closure evidence. It is
control-plane evidence only.
```

## Stage 74: R-Scaling Boundary

Goal:

```text
Test whether directly increasing PVW/MAT-SAB lane count beyond r=4 improves
complete SAB throughput under the current active-buffer MAT path.
```

Tasks:

- add H10 for direct `r>4` lane scaling;
- run complete-SAB smoke for `r=6` and `r=8` under `spqlios_avx512`,
  `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and
  `SAB_PVW_ACTIVE_BUFFER_FUSION=true`;
- compare the smoke results against the Stage36 r=4 10-run reference;
- record a candidate variant card, theory check, experiment plan, decision
  CSV, and log.

Gate:

- r=6 and r=8 complete-SAB correctness must pass;
- r=6 and r=8 must remain faster than repeated scalar SAB to be useful as
  scaling-boundary evidence;
- direct r>4 promotion requires beating the current r=4 promoted evidence
  before repeated/noise/resource gates are justified;
- no scalar SAB path, default `sab_pvw_*` path, key format, novelty,
  theorem-level, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage74 passed as a negative boundary. r=6 and r=8 complete-SAB smoke runs
passed correctness and remained faster than repeated scalar SAB, but their
one-run speedups, 1.251x and 1.199x, were below the Stage36 r=4 10-run CI
lower bound 1.314893. Direct r>4 lane-count expansion is not promoted without
a new r>4-specific kernel/layout/sparse-MAT hypothesis.
```

## Stage 75: R>4 Profile Boundary Diagnosis

Goal:

```text
Explain the Stage74 r>4 boundary by checking whether r=6/r=8 preserve the
exact SAB schedule counts and by attributing the remaining cost to MAT/body
work.
```

Tasks:

- run body-profile complete-SAB smokes for `r=6` and `r=8` under the same
  `spqlios_avx512`, specialized MAT-AVX512, active-buffer path as Stage74;
- verify exact target counts:
  `cmux_calls == mat_ep_calls == 573440`, `ncmux_calls == 5080`,
  `sub_a_calls == 39`, and active-buffer `copyback_calls == 0`;
- parse raw `SAB_PVW_BODY_PROFILE` logs into `profile_metrics.csv` so the
  r>4 boundary has component attribution;
- update H10 and the completion route so future large-r work starts from a
  dedicated r>4 layout/kernel/sparse-MAT hypothesis rather than direct lane
  scaling.

Gate:

- r=6 and r=8 complete-SAB correctness and count gates must pass;
- Stage74 must remain not promoted unless repeated full-SAB evidence beats
  the current r=4 promoted boundary;
- if counts fail, fix the schedule model before optimizing r>4;
- no scalar SAB path, default `sab_pvw_*` path, key format, novelty,
  theorem-level, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage75 passed as a profile-backed boundary. r=6 and r=8 preserve the exact
target schedule: CMUX/MAT EP 573440, NCMUX 5080, sub_a 39, and active-buffer
copyback 0. The profile samples show MAT EP is about 55% of full body time
for both r=6 and r=8, so direct r>4 underperformance is attributed to
per-update MAT/body cost under invariant schedule counts. Direct r>4 remains
not promoted; future large-r work requires a new r>4-specific layout, tiling,
register/cache-blocking, or sparse/structured-MAT hypothesis.
```

## Stage 76: R>4 Kernel Feasibility

Goal:

```text
Check whether the current generic r=6/r=8 MAT external-product kernel is
itself a viable promotion candidate, or whether the next large-r step must
start from a new fused MAT multiply/layout hypothesis.
```

Tasks:

- add an explicit `SAB_PVW_RGT4_KERNEL_TEST` harness that exercises r=6/r=8
  MAT_TRGSW/PVW identity-lane checks and kernel microbenchmarks;
- parse DFT-output and full-output MAT-vs-scalar microbenchmarks into
  `kernel_microbench.csv`;
- parse scalar repeated and MAT shared-mask `EP_BREAKDOWN` rows into
  `ep_breakdown.csv`;
- add H11 for a future fused r>4 MAT kernel and keep it explicitly
  unimplemented/not promoted;
- update the route-to-completion policy so future r>4 work targets dense MAT
  multiply/layout/register pressure rather than another direct lane-count
  increase.

Gate:

- r=6 and r=8 identity-lane correctness must pass;
- current r>4 promotion requires DFT-output MAT to beat repeated scalar
  external products, not only full-output shared-decomposition/DFT benefit;
- if MAT shared-mask phase is multiply dominated, future work must target
  fused MAT multiply or layout/register blocking;
- no scalar SAB path, default `sab_pvw_*` path, key format, novelty,
  theorem-level, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage76 passed as a diagnostic negative/not-promoted kernel boundary. The
generic r=6/r=8 MAT path passes identity-lane correctness, but DFT-output
MAT is 0.984x/0.912x versus repeated scalar external products. Full-output
MAT is only 1.168x/1.044x, and MAT shared-mask multiply share rises to
55.72%/61.20%. Current r>4 MAT kernel scaling is not promoted; the next
large-r implementation hypothesis is a fused MAT multiply/layout/register-
blocking kernel with full correctness and complete-SAB gates.
```

## Stage 77: R>4 Fused MAT Kernel Smoke

Goal:

```text
Implement the H11 fused r>4 MAT external-product kernel behind an explicit
flag and test whether the kernel signal propagates to complete SAB smoke.
```

Tasks:

- add `MAT_TRGSW_AVX512_RGT4_FUSED` as an explicit experimental flag;
- add a tiled AVX512 kernel for `k=1`, `l=1`, `r=6` and `r=8`;
- compare generic and fused r>4 kernel logs under the same Stage76 harness;
- run complete-SAB one-run smokes for generic and fused r=6/r=8;
- aggregate the kernel and full-SAB evidence into Stage77 CSV/MD artifacts;
- update H11 and the completion route so positive smoke leads to repeated
  gates, not immediate promotion.

Gate:

- generic and fused r=6/r=8 kernel correctness must pass;
- fused must beat generic in DFT-output and full-output microbench;
- fused complete-SAB one-run smoke must beat same-stage generic r>4;
- r>4 may not be promoted until repeated full-SAB, noise, and resource gates
  pass;
- no scalar SAB path, default `sab_pvw_*` path, key format, novelty,
  theorem-level, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage77 passed as a positive smoke candidate, not a promoted path. The fused
tiled kernel beats same-stage generic r>4 in DFT-output microbench
(`1.582x` r=6, `1.431x` r=8) and full-output microbench (`1.510x` r=6,
`1.370x` r=8). Complete-SAB one-run fused/generic is `1.120x` for r=6 and
`1.102x` for r=8. Promotion remains blocked: r=8 DFT-output is still below
repeated scalar, r=8 full-SAB remains below the r=4 reference, and both r
values need repeated full-SAB/noise/resource gates. Stage78 should test r=6
as the main candidate and r=8 as a stress case.
```

## Stage 78: R>4 Fused Repeated Gates

Goal:

```text
Test whether the Stage77 H11 fused r>4 MAT kernel remains positive under
repeated complete-SAB, final-output noise, and resource gates.
```

Tasks:

- add a Stage78 runner that explicitly sets
  `MAT_TRGSW_AVX512_RGT4_FUSED=true`, `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`,
  and `SAB_PVW_ACTIVE_BUFFER_FUSION=true`;
- run r=6 complete-SAB repeated A/B as the main promotion screen;
- run r=8 complete-SAB as a large-r stress case;
- run r=6/r=8 final-output noise and correctness seeds;
- run r=6/r=8 resource accounting for PVW and repeated scalar modes;
- aggregate all results into full-SAB, noise, resource, summary, and log
  artifacts without changing default paths.

Gate:

- Stage77 must already be recorded as
  `PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED`;
- r=6 repeated full-SAB must have at least three passing process samples and
  min speedup greater than 1.0;
- r=6 mean speedup must be compared against the Stage36 r=4 10-run mean and
  CI95 lower bound;
- r=6/r=8 final-output noise must have zero PVW/scalar/pair failures;
- resource overhead must be reported with the speedup evidence;
- no scalar SAB path, default `sab_pvw_*` path, key format, novelty,
  theorem-level, all-parameter, or hardware-counter claim is upgraded.

Status:

```text
Stage78 passed as a promotion candidate, not a default change. r=6 complete
SAB repeated A/B has 3 passing samples with mean speedup 1.408x, min 1.361x,
and max 1.435x, exceeding the Stage36 r=4 reference mean 1.377x and CI95 low
1.314893. r=8 stress passes one full-SAB sample at 1.350x. r=6/r=8
final-output noise has 3 seeds each with zero PVW/scalar/pair failures.
Resource accounting records key ratios 1.122537/1.181090 and RSS ratios
1.030750/1.071251 for r=6/r=8. The next step is Stage79 high-stat
confirmation before any default/path promotion or stronger claim change.
```

## Stage 79: R>4 Fused High-Stat Confirmation

Goal:

```text
Confirm or reject the Stage78 r=6 promotion candidate with enough repeated
complete-SAB and noise evidence to compare it fairly with the Stage36 r=4
high-stat reference.
```

Tasks:

- run r=6 fused complete-SAB A/B with at least 10 process samples under the
  same `spqlios_avx512` backend and flags as Stage78;
- run r=6 final-output noise with at least 20 seeds, preferably 50 if runtime
  budget permits;
- repeat resource accounting enough to determine whether keygen/RSS overhead
  is stable;
- compare r=6 fused against Stage36 r=4 and against Stage78 itself using
  mean, min/max, standard deviation, and confidence interval;
- decide whether H11 becomes promoted, remains a candidate, or is rejected.

Gate:

- all complete-SAB samples must pass correctness;
- noise failures must stay at zero or be explained by a parameter/security
  adjustment before promotion;
- r=6 fused must preserve a practical throughput advantage after resource
  overhead is reported;
- if the confidence interval overlaps r=4 without clear practical gain, mark
  the result as inconclusive rather than promoted.

Status:

```text
Completed as high-stat evidence recorded, review required. r=6 fused complete
SAB A/B has 10 passing process samples with mean speedup 1.367x, min 1.314x,
max 1.457x, stddev 0.040977, and CI95 [1.341302, 1.392098]. This is above
the Stage36 r=4 CI95 low 1.314893 but below the Stage36 r=4 mean 1.377x, so
it does not strongly confirm automatic promotion over the r=4 reference.
r=6 final-output noise passes 20 seeds with zero PVW/scalar/pair failures and
avg PVW-minus-scalar log2 gap -0.107800. Resource accounting passes 3 runs
with key ratio 1.122537 and RSS ratio mean/max 1.030715/1.030764. The Stage79
decision is PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED.
```

## Stage 80: Promotion Integration Or Rejection Audit

Goal:

```text
If Stage79 confirms the r=6 fused candidate, decide how it is exposed without
breaking scalar SAB or the existing r=2/r=4 path. If Stage79 does not confirm
it, record the candidate as neutral/rejected and return to variant triage.
```

Tasks:

- keep scalar `sab_rlwe_bootstrap` unchanged;
- keep r=2/r=4 defaults unchanged unless a separate gate justifies a default
  change;
- expose r=6 fused only behind an explicit flag or documented `sab_pvw_*`
  variant unless promotion policy is satisfied;
- rerun current-head scalar/PVW smoke, repeated full-SAB continuity, noise,
  resource, frontier, closure, and verifier checks after any integration
  change.

Gate:

- no default behavior changes without a passing current-head refresh;
- verifier and artifact manifest must include the promoted or rejected status;
- claim wording must distinguish r=6 fused engineering evidence from the
  existing r=2/r=4 scoped baseline.

Status:

```text
Completed. Stage80 reads the Stage79 high-stat result, runs current-head smoke,
checks static default-path guards, and records
PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED. H11 r=6 fused MAT remains
available only behind the explicit MAT_TRGSW_AVX512_RGT4_FUSED flag; it is
not promoted, not made default, and does not change scalar SAB or the existing
r=2/r=4 scoped promoted path. Stage81 is now the next local variant triage
entry.
```

## Stage 81: Next Variant Triage

Goal:

```text
After the H11 r=6 fused decision, select the next local optimization only if
the current evidence identifies a bottleneck that can be falsifiably improved.
```

Candidate directions:

- sparse/structured MAT layout that reduces dense `(1+r)^2` work;
- r=8-specific register/cache tiling if Stage79 leaves r=6 strong but r=8
  weak;
- SAB schedule/body fusion only if post-Stage79 profiles show non-MAT costs
  dominate;
- post-processing or extraction changes only if tail cost rises above the
  Stage24 threshold.

Gate:

- every candidate must have a hypothesis, theory check, isolated correctness
  gate, full-SAB A/B gate, noise/resource gate, and promote/neutral/reject
  decision.

Status:

```text
Completed. Stage81 does not select a new hot-path implementation. It records
that H3 sparse/structured MAT shortcuts remain blocked by key-format/security
design, direct r>4/r=8 tiling is not justified after Stage74-80, and
post-processing remains below the Stage24 threshold. The selected next local
engineering action is profile-only post-H11 fused r=6 attribution before any
new SAB/MAT optimization hypothesis is opened.
```

## Stage 82: Post-H11 Fused R6 Profile Attribution

Goal:

```text
Run the profile-only attribution required by Stage81 on the explicit H11 fused
r=6 path before opening any new local SAB/MAT implementation hypothesis.
```

Tasks:

- run `SAB_PVW_BODY_PROFILE` for `r=6` with
  `MAT_TRGSW_AVX512_RGT4_FUSED=true`;
- confirm target correctness and exact schedule counts;
- record component shares for MAT EP, from_DFT, add/sub, NCMUX, sub_a, and
  non-MAT body cost;
- compare only as profile attribution, not as a final latency claim.

Gate:

- schedule counts must remain CMUX/MAT EP `573440`, NCMUX `5080`, sub_a `39`,
  and active-buffer copyback `0`;
- Stage80 policy must remain unchanged: H11 is explicit experimental only;
- no new speedup or default-path claim can be made from the instrumented
  profile timing.

Status:

```text
Completed. Stage82 profiles the explicit H11 fused r=6 path and records
PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY. The profile run preserves
target schedule counts and active-buffer copyback=0. Instrumented profile
speedup is 1.405x, recorded only for attribution. MAT EP is 47.6916% of full
body time, from_DFT is 21.7231%, add is 13.6870%, sub is 13.4137%, and
non-MAT body time is 52.3084%. The next local work is a theory/design check
for reducing dense MAT body work without key-format risk; no new code path is
promoted.
```

## Stage 83: MAT Body Reduction Theory/Design Check

Goal:

```text
Convert the Stage82 post-H11 fused r=6 profile into a concrete MAT-body
optimization route without writing hot-path code or changing scalar/default
behavior.
```

Tasks:

- screen candidate MAT body reductions from the Stage82 profile;
- separate low-risk no-key-format candidates from blocked sparse/selector
  arithmetic shortcuts;
- record Amdahl-style bounds so a MAT-body-only kernel result is not
  overclaimed as full bootstrapping acceleration;
- choose the next local preflight only if it has staged correctness,
  microbench, full-SAB A/B, noise/resource, and promote/neutral/reject gates.

Gate:

- Stage81 profile-first policy and Stage82 MAT-body-primary profile must be
  present;
- any sparse selector shortcut remains blocked unless a new key-format and
  security argument exists;
- the selected candidate must not alter scalar SAB or default `sab_pvw_*`;
- no speedup, novelty, theorem-level, or hardware-counter claim is upgraded.

Status:

```text
Completed. Stage83 records
PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT. The selected
Stage84 local preflight is H13-C1: an explicit r=6 full-output tile sweep for
the r>4 MAT body. It is selected only as a preflight because it can reduce
dec-row reloads without changing key format, while dense m^2 selector/FMA work
remains unchanged and register pressure may erase the gain. Sparse selector
skipping remains blocked by key-format/security requirements. Stage83 does not
promote code or change claim scope.
```

## Stage 84: H13 R6 MAT Tile-Sweep Preflight

Goal:

```text
Test the selected Stage83 r=6 MAT full-output tile hypothesis behind an
explicit flag or isolated harness before any full-SAB promotion campaign.
```

Tasks:

- add an explicit flag or isolated kernel path for r=6 full-output tile
  accumulation;
- compare against the current `MAT_TRGSW_AVX512_RGT4_FUSED` tile-of-4 path;
- run identity-lane MAT/PVW correctness;
- run DFT-output and full-output MAT microbench under the same backend;
- inspect objdump and native counters when available for spills/load changes;
- run non-instrumented complete-SAB A/B only if the kernel signal is positive.

Gate:

- scalar/default paths remain unchanged;
- any correctness failure rejects the candidate;
- a kernel win without full-SAB propagation remains kernel-only evidence;
- no promotion occurs until Stage85 repeated/noise/resource gates pass.

Status:

```text
Completed. Stage84 implements `MAT_TRGSW_AVX512_R6_FULLTILE=true` behind an
explicit flag. Kernel correctness passes and r=6 MAT microbench is mildly
positive versus the current r>4 tile4 fused path: DFT-output `1.036x` and
full-output `1.021x`. The complete-SAB r=6 one-run smoke is not positive:
fulltile/tile4 is `0.974x`, with scalar speedup dropping from `1.392x` to
`1.328x`. The decision is
PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED. Stage85 is not opened
from this evidence; the local route moves to Stage86 candidate routing.
```

## Planned Stage 85: H13 Full-SAB Promotion Gate

Goal:

```text
If Stage84 is positive, decide whether the H13 candidate improves complete
SAB throughput enough to become a promoted explicit variant.
```

Tasks:

- run repeated complete-SAB A/B for the positive Stage84 candidate;
- run final-output noise and resource gates for the candidate r values;
- compare against Stage36 r=4 promoted evidence and Stage79 r=6 H11 evidence;
- classify the candidate as promote, neutral, or reject.

Gate:

- repeated full-SAB correctness must pass;
- final-output noise failures must not exceed baseline under tested scope;
- key size, keygen time, RSS, and scratch overhead must be reported;
- promoted wording must remain scoped and same-backend.

Status:

```text
Not opened after Stage84 because the r=6 tile-sweep preflight did not improve
complete-SAB smoke. This stage remains conditional on a future Stage84-style
candidate that is positive at full-SAB level.
```

## Stage 86: Secondary CMUX Materialization Pass

Goal:

```text
If MAT-body preflight is neutral or exposes a new balance, revisit the
Stage82 non-MAT body share without repeating the known neutral Stage18/23
epilogue-only fusions.
```

Tasks:

- profile from_DFT/add/sub after any Stage84/85 candidate;
- design only schedule-window or lifetime reductions that are distinct from
  prior neutral epilogue fusions;
- validate per-CMUX phase equivalence and complete-SAB A/B.

Gate:

- do not pursue if refreshed non-MAT share is not material;
- any materialization optimization must beat complete-SAB repeated A/B, not
  just profile counters.

Status:

```text
Completed as a design gate. Stage86 reads the Stage82 r=6 profile and the
Stage84 not-promoted decision, confirms that non-MAT CMUX/body work remains
material (`52.31%` full-body share, with `from_DFT+add=35.41%` and
`sub=13.41%`), rejects repeating Stage18/23 epilogue-only fusions, and
selects H14-C1 backend `FromDFT+add` materialization callback as the next
explicit preflight. No code path is promoted and no complete-SAB speedup
claim is upgraded by this stage.
```

## Stage 87: H14 Backend FromDFT-Add Preflight

Goal:

```text
Implement the Stage86-selected H14-C1 backend materialization candidate behind
an explicit flag and run correctness plus one-run complete-SAB smoke against
the wrapper-level fused baseline.
```

Tasks:

- add `SAB_PVW_BACKEND_FROM_DFT_ADD` without changing scalar/default paths;
- add backend torus64 `FromDFT+add` materialization writeback;
- run WSL `spqlios_avx512` staged CMUX/RGSW/MAT and target full-output gates;
- compare r=6 wrapper fused FromDFT-add versus backend FromDFT-add complete
  SAB one-run smoke.

Gate:

- explicit flag only; no scalar/default behavior change;
- correctness gates pass before interpreting performance;
- one-run full-SAB smoke is positive before opening repeated gates;
- no promotion from one-run smoke.

Status:

```text
Completed as a preflight. Stage87 implements `SAB_PVW_BACKEND_FROM_DFT_ADD`.
WSL `spqlios_avx512` staged CMUX/NCMUX/RGSW/MAT and target full-output gates
pass. In r=6 one-run complete-SAB smoke, wrapper fused FromDFT-add PVW latency
is `40196035.000 us` and backend FromDFT-add is `38284667.000 us`, giving a
backend-vs-wrapper latency ratio of `1.049925x`. This is a promotion candidate
only. Stage88 later repeated the candidate and Stage89 completed policy
integration without changing defaults.
```

## Stage 88: H14 Repeated/Noise/Resource Gate

Goal:

```text
Decide whether the Stage87 H14-C1 backend materialization preflight should be
promoted, kept experimental, or rejected.
```

Tasks:

- run repeated r=6 complete-SAB A/B for wrapper fused versus backend-add under
  the same `spqlios_avx512` backend;
- run at least target full-output correctness and final-output noise gates;
- record key size, RSS, keygen time, and any backend-specific constraints;
- update Stage50/51/57/59/68/42 closure and read-only verifier.

Gate:

- repeated complete-SAB speedup is stable, not a single-run artifact;
- scalar SAB remains runnable and comparable;
- resource/noise costs are reported with the speedup.

Status:

```text
Completed as a repeated gate. Stage88 keeps `SAB_PVW_BACKEND_FROM_DFT_ADD`
explicit and leaves scalar/default paths unchanged. Under WSL
`spqlios_avx512`, r=6 backend-vs-wrapper complete-SAB latency ratio is
`1.035516x` over three paired runs, with per-run minimum `1.024476x`.
Backend-vs-repeated-scalar speedup averages `1.437x` with minimum `1.435x`.
Final-output noise passes three seeds with zero PVW/scalar/pair failures.
Resource accounting records key ratio `1.122537x`, keygen ratio
`1.301382x`, and RSS ratio `1.030722x`. This records H14-C1 as a promotion
candidate only. Stage89 later promotes it as a preferred explicit r=6
engineering path while keeping defaults and paper-level claims unchanged.
```

## Stage 89: H14 Promotion Policy Integration

Goal:

```text
Decide how the Stage88 H14-C1 backend FromDFT-add promotion candidate should
be exposed: promoted for the explicit r=6 experimental path, kept behind an
opt-in flag, or rejected despite positive Stage88 evidence.
```

Tasks:

- run current-head smoke for scalar binary, scalar ternary build, and explicit
  backend PVW target gate;
- verify `SAB_PVW_BACKEND_FROM_DFT_ADD` remains explicit and does not change
  scalar/default SAB behavior;
- compare Stage88 evidence against Stage79/80 policy precedent and Stage36
  r=4 reference evidence;
- update hypothesis status and claim wording to separate backend engineering
  improvement from final default bootstrapping acceleration.

Gate:

- current-head smoke passes;
- no default path or scalar behavior changes;
- policy decision is promote/keep/reject with reproducible evidence and no
  overclaim.

Status:

```text
Completed as a policy integration. Stage89 current-head smoke passes for the
default scalar binary full run, explicit H14 backend PVW target gate, and
scalar ternary build. `SAB_PVW_BACKEND_FROM_DFT_ADD` remains explicit and
default false. Stage89 compares Stage88 against the Stage36 r=4 reference and
Stage80 promotion-policy precedent: backend-vs-wrapper repeated latency ratio
is `1.035516x` mean and `1.024476x` min; backend-vs-repeated-scalar speedup is
`1.437x` mean and `1.435x` min; Stage36 r=4 mean is `1.377x` with CI
`[1.314893,1.438107]`. The decision is
`PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT`: H14-C1 is the
preferred explicit r=6 local engineering path, but scalar/default paths and
paper-level novelty/theory claims remain unchanged.
```

## Stage 90: External Claim Unlock

Goal:

```text
Unlock stronger paper/theory claims that are intentionally blocked in the
current local environment.
```

Tasks:

- rerun native perf-counter attribution on native Linux or perf-enabled WSL
  before claiming MAT-AVX512 load/store/FMA optimality;
- register and manually inspect the 2025/686 full text before theorem-level
  algorithm, noise, security, table, figure, or experiment citations;
- complete related-work claim-to-source review before novelty wording.

Gate:

- native perf must provide hardware counters, not only WSL proxy evidence;
- full-text review must have source anchors;
- novelty claims must be downgraded if related work already covers the idea.

Status:

```text
Completed as an external-claim probe. Stage90 reruns a fresh 2025/686
citation/full-text route probe, native perf-counter gate, and external
evidence intake after Stage89 promoted H14-C1 as the preferred explicit r=6
local engineering path. The probe records
PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED:
direct ePrint/ACM/ResearchGate full-text routes remain blocked, no reviewed
FAB686_FULLTEXT_PATH artifact is registered, `perf` is missing in the current
WSL2 PATH, and novelty/source review still lacks source anchors.

Stage90 therefore does not upgrade any theorem-level 2025/686 citation,
novelty, or MAT-AVX512 hardware-counter optimality claim. It only closes the
current external-claim probe and makes Stage91 responsible for freezing a
scoped final package unless the user supplies external evidence for another
unlock pass.
```

## Stage 91: Final SAB Optimization Package

Goal:

```text
Freeze the final engineering and paper/release package after all promoted
variants and external claim unlocks are either complete or explicitly scoped
out.
```

Tasks:

- produce final algorithm description, complexity model, experiment tables,
  resource/noise/security discussion, negative ablations, and reproduction
  commands;
- run final smoke, performance, noise, resource, closure, and verifier checks;
- record exactly which claims are engineering-supported, paper-ready, blocked,
  or out of scope.

Gate:

- scalar baseline is still runnable and comparable;
- complete-SAB benchmark evidence supports every speedup claim;
- algorithmic gains are separated from backend/SIMD gains;
- reproduction pack includes commit, command, backend, CPU flags, logs,
  summaries, and decisions.

Status:

```text
Completed as the final scoped SAB optimization package. Stage91 records
PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED. The package freezes
the current engineering evidence without rerunning heavy benchmarks: Stage89
current-head smoke is inherited because no SAB source files changed after the
Stage89 promotion-policy commit; Stage36 remains the high-stat complete-SAB
performance source for target r=2/r=4; Stage88/89 define H14-C1 as the
preferred explicit r=6 engineering path, not a default or paper-level claim;
Stage36/88 noise and resource gates are reported under their recorded scopes;
and Stage90 keeps native-perf, 2025/686 full-text, and novelty/source-review
claims blocked.

The final package artifacts are `docs/stage91_final_sab_optimization_package.md`
and `repro/stage91_final_package/`. Stage91 does not mark novelty,
theorem-level 2025/686 citations, non-binary PVW-SAB, all-parameter speedup,
or MAT-AVX512 theoretical optimality as supported.
```

## Stage 92: External Unlock Execution Packet

Goal:

```text
Convert the remaining post-Stage91 stronger-claim blockers into executable
external unlock lanes with explicit commands, expected artifacts, acceptance
gates, failure policy, and claim effects.
```

Tasks:

- record the native/perf lane for CB5 without treating WSL proxy evidence as
  hardware-counter proof;
- record the 2025/686 full-text lane for CB7 without treating metadata or
  blocked download routes as theorem-level evidence;
- record the novelty/source-anchor lane for CB6 without upgrading novelty
  wording before manual review;
- record the final-refresh route that reruns final audit, Stage90, Stage91,
  and closure verification after external evidence changes.

Gate:

- Stage91 must remain
  `PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED`;
- CB5, CB6, CB7, and A9 must remain visible in the blocker dashboard;
- every external lane must have a command, expected artifacts, acceptance
  gate, failure policy, and claim effect;
- Stage92 must preserve the Stage91 claim boundary and must not mark any
  stronger claim as supported.

Status:

```text
Completed as an external unlock execution handoff. Stage92 records
PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED. The
packet names the exact commands for native/perf Stage28, 2025/686 full-text
Stage38, external evidence registration, novelty review, and final refresh.
It does not execute native perf, fetch or review full text, or upgrade any
novelty/theory/paper-level claim.
```

## Stage 93: External Lane Attempt

Goal:

```text
Execute the Stage92 lanes that can be checked in the current environment:
native-perf availability and local 2025/686 full-text artifact search.
```

Tasks:

- run the Stage28 native perf gate into a Stage93-specific output directory
  so historical Stage28 artifacts are not overwritten;
- search configured local roots for a recognized 2025/686 full-text filename
  candidate;
- read external evidence intake and confirm whether any supplied artifact can
  move CB5/CB7/CB6 beyond blocked;
- preserve Stage91/92 claim guards unless the acceptance gates actually pass.

Gate:

- Stage92 must be passed before Stage93 is interpreted;
- native perf attempt must be recorded, even if blocked;
- local full-text search must be recorded, even if no candidate exists;
- external intake status and claim guard must remain visible.

Status:

```text
Completed as a current-environment external lane attempt. Stage93 records
PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED. Current
WSL2 still lacks `perf` in PATH, so native hardware-counter attribution remains
blocked. No recognized local 2025/686 full-text candidate is found in the
configured search roots, and external evidence intake still reports missing
full text and missing native perf summary. Stronger claims remain blocked.
```

## Stage 94: Local Frontier Audit

Goal:

```text
After the Stage93 external lane attempt, determine whether any remaining local
PVW/MAT-SAB hot-path candidate is justified before writing more code.
```

Tasks:

- aggregate Stage69, Stage81/82, Stage84, Stage86, Stage89, Stage91, and
  Stage93 evidence into a candidate frontier;
- keep H14-C1 backend FromDFT-add as the preferred explicit r=6 local path if
  Stage89 still passes;
- quantify the H14-C3 dual-butterfly fallback using the Stage82 sub-share and
  Amdahl ceiling;
- preserve deferred/rejected decisions for post-processing tail, H13 tile
  sweep, sparse selector, blind AVX512 layout work, and non-binary PVW-SAB;
- prove no SAB source or default-path change happened after the Stage89 policy
  anchor.

Gate:

- all input stage decisions must match their scoped statuses;
- H14-C1 must remain explicit/default false;
- no unblocked local hot-path candidate may remain in the frontier;
- C3/C4/C5 stronger claims must remain blocked.

Status:

```text
Completed as a post-Stage93 local frontier audit. Stage94 records
PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH. H14-C1 remains the preferred
explicit r=6 engineering path; H14-C3 is deferred because Stage82 gives
CMUX sub share `0.134137`, so even halving it has only `1.071890` body-level
ceiling. H13 r=6 tile sweep stays rejected for full-SAB promotion, the
post-processing tail remains below threshold, sparse-selector skipping remains
unsafe without a new key/security design, further AVX512 layout work still
needs native counters or a distinct falsifiable hypothesis, and non-binary
PVW-SAB remains blocked on reviewed 2025/686 branch semantics.
```

## Stage 95: Public Source Reprobe

Goal:

```text
Refresh public 2025/686 source routes after Stage94 and decide whether the
full-text or novelty blockers can move.
```

Tasks:

- rerun the Stage72 external source refresh;
- summarize author metadata, DOI metadata, GitHub code route, ePrint PDF,
  ACM PDF, and author-site PDF availability;
- keep metadata/code visibility separate from reviewed theorem-level full
  text;
- preserve Stage91 claim guard unless an actual PDF/text artifact becomes
  locally available and Stage38/manual review gates pass.

Gate:

- Stage94 must pass first;
- Stage72 current source refresh must pass;
- metadata/code route visibility must not be treated as reviewed full text;
- direct PDF/text route accessibility is required before CB7 can move.

Status:

```text
Completed as a public-source reprobe. Stage95 records
PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED. Author metadata,
author BibTeX, DOI metadata, and the GitHub code route are visible, but the
ePrint PDF and ACM PDF routes still report `403`, and the author-site guessed
PDF reports `404`. Therefore public metadata improves citation context but
does not unlock theorem-level 2025/686 source review, novelty claims, or
paper-level claim upgrades.
```

## Stage 96: Upstream Delta Audit

Goal:

```text
Record the provenance boundary between the public 2025/686 implementation
route (`origin/main`) and the local PVW/MAT-SAB optimization chain.
```

Tasks:

- fetch `origin` and resolve `origin/main`, `HEAD`, merge-base, ahead count,
  and behind count;
- classify all files changed since `origin/main` by source/docs/repro/theory
  area;
- verify tracked PVW/MAT-SAB experiment flags remain default-false in
  `src/mosfhet/Makefile.def`;
- keep code-route provenance separate from theorem-level 2025/686 full-text
  review, novelty, and hardware-counter optimality claims.

Gate:

- Stage95 must still report
  `PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED`;
- `origin/main` must resolve and be the current merge-base of `HEAD`;
- local branch may be ahead, but must not be silently behind unreviewed
  upstream changes;
- default flag guard must pass;
- Stage91 C3/C4/C5 stronger claim boundaries must remain blocked or
  missing-optional.

Status:

```text
Completed as an upstream/local provenance audit. Stage96 records
PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED. After fetching
origin, `origin/main=d251d06` is the merge-base of `HEAD=986f42f`, local HEAD
is ahead by 255 commits and behind by 0, and the local delta contains 1681
changed files. The delta classification records 5 PVW/MAT-SAB source files,
20 other source/backend files, and the remaining docs/scripts/repro/theory
evidence files. All tracked PVW/MAT-SAB experiment flags remain default-false.
This supports reproducibility and code provenance only; it does not upgrade
theorem-level 2025/686, novelty, or MAT-AVX512 hardware-counter claims.
```

## Stage 97: Source Delta Guard

Goal:

```text
Turn the Stage96 upstream/local source-delta boundary into a reusable
pre-flight guard for future PVW/MAT-SAB changes, proving that scalar/default
SAB separation, experimental build flags, and current smoke evidence remain
machine-checkable.
```

Tasks:

- inventory source and hot-path deltas under `main.c`, `include/`, and `src/`
  relative to `origin/main`;
- scan scalar SAB files for forbidden PVW/MAT-SAB symbols;
- scan selected shared MOSFHET backend files for `sab_pvw` symbols;
- verify all tracked PVW/MAT-SAB, AVX512, profile, and microbench flags remain
  default-false;
- verify `pvwtmlwe.c` and `mattrgsw.c` are compiled only under
  `ENABLE_PVW_TMLWE=true`;
- bind the guard to Stage33 and Stage89 scalar/default smoke evidence.

Gate:

- Stage96 must still report
  `PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED`;
- source delta inventory must be non-empty and classified;
- scalar SAB files must contain no `SAB_PVW`, `sab_pvw`, `PVW_TMLWE`, or
  `MAT_TRGSW` tokens;
- selected shared backend files must contain no `SAB_PVW` or `sab_pvw` tokens;
- all tracked flags must remain default-false and PVW/MAT sources must remain
  gated;
- Stage33 and Stage89 scalar binary/ternary smoke evidence must still pass.

Status:

```text
Completed as a source isolation guard. Stage97 records
PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED. The source delta
inventory classifies 26 source/hot-path files, including 5 explicit PVW/MAT
files and 4 scalar SAB files under symbol guard. Scalar SAB files contain no
forbidden PVW/MAT-SAB tokens, selected shared backend files contain no
`sab_pvw` tokens, all tracked PVW/MAT-SAB/AVX512/profile/microbench flags are
default-false, and PVW/MAT sources remain gated by `ENABLE_PVW_TMLWE`.
Stage33 and Stage89 scalar binary/ternary smoke evidence remains passing.
This is a guardrail and reproducibility result only; it does not upgrade any
speedup, novelty, theorem-level, or hardware-counter claim.
```

## Stage 98: Current-Head Smoke Refresh

Goal:

```text
Refresh current-head smoke evidence after Stage97 so scalar/default SAB,
explicit active-buffer PVW, explicit H14 backend PVW, and scalar ternary build
continuity are directly proven on the latest committed code state.
```

Tasks:

- run the default scalar binary full program for `BINARY SET_2_3_2048`;
- run the explicit active-buffer PVW target full bootstrap gate;
- run the explicit H14 backend FromDFT-add PVW target full bootstrap gate;
- build the scalar ternary target to preserve non-binary scalar independence;
- preserve raw build/run logs and aggregate them into a machine-checkable
  summary;
- keep the result scoped to current-head smoke continuity.

Gate:

- Stage97 must still report
  `PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED`;
- scalar binary run must end with `Pass`;
- active-buffer PVW target gate must print
  `SAB_PVW target full bootstrap gate: Pass`;
- H14 backend PVW target gate must print
  `SAB_PVW target full bootstrap gate: Pass`;
- scalar ternary build must complete;
- raw build/run logs must be present.

Status:

```text
Completed as a current-head smoke refresh. Stage98 records
PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH. On `HEAD=e89b76f`, the default scalar
binary full run passes, the explicit active-buffer PVW target full bootstrap
gate passes, the explicit H14 backend PVW target full bootstrap gate passes,
and the scalar ternary build passes. Raw build/run logs are preserved under
`repro/stage98_current_smoke_refresh/`. This is current-head continuity
evidence only; it does not upgrade speedup, novelty, theorem-level, or
hardware-counter claims.
```

## Stage 99: External Blocker Reprobe

Goal:

```text
After Stage98 current-head smoke continuity, reprobe the remaining external
blockers and current Codex goal route: native perf, public 2025/686 routes,
local 2025/686 full-text availability, and novelty/source-review state.
```

Tasks:

- run the lightweight Stage28 native perf-counter probe in a Stage99 output
  directory;
- rerun the Stage27 citation/source access probe in a Stage99 output
  directory;
- search configured local roots for 2025/686 full-text candidates;
- register the current Codex goal and completion route in
  `docs/current_codex_goal_sab_completion.md`;
- if a full-text candidate is found, run Stage38 to register the artifact and
  keep theorem-level claims blocked until manual source-anchor review.

Gate:

- Stage98 must report `PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH`;
- native perf remains blocked unless hardware counters are usable and a correct
  benchmark run is recorded under perf;
- full-text availability moves only to review-required until Stage38 checklist
  rows are filled with concrete anchors;
- novelty remains blocked until manual related-work/source review is complete;
- no Stage99 result may be used as a new speedup or novelty claim.

Status:

```text
Completed as an external blocker reprobe. Stage99 records
PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED. Native perf remains
blocked in the current WSL2 environment because `perf` is unavailable. Direct
public 2025/686 PDF routes remain blocked or metadata-only, but local search
found `/mnt/c/Users/spremez/Documents/BTS/papers/eprint-2025-686.pdf` and
Stage38 registered it as a hashed PDF artifact. The final state is therefore
`SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED`: the scoped
engineering PVW/MAT-SAB chain remains ready, while theorem-level 2025/686,
novelty, and MAT-AVX512 hardware-counter claims still require manual review or
native-perf evidence.
```

## Stage 100: Full-Text Anchor Prefill

Goal:

```text
Use the Stage99/Stage38 registered 2025/686 PDF to generate candidate
page-level anchors for the Stage38 manual review checklist, without storing
full paper text and without upgrading any theorem-level, novelty, or
MAT-AVX512 optimality claim.
```

Tasks:

- parse the registered local PDF with `pdftotext` into a temporary file only;
- split the paper by page and search predefined protocol, complexity,
  correctness/noise, parameter/security, PVW-SAB delta, and novelty-boundary
  keyword sets;
- write candidate page/keyword metadata to
  `repro/stage100_fulltext_anchor_prefill/`;
- prefill `repro/stage38_fulltext_review_gate/review_checklist.csv` with
  candidate-only page lists;
- keep all checklist rows in review-required status until a human verifies
  the PDF pages and replaces candidates with exact source anchors.

Gate:

- Stage99 must report
  `PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED`;
- `fab686_fulltext` must be `AVAILABLE_UNREVIEWED` and point to an existing
  PDF;
- candidate anchors must remain review-required;
- no Stage100 result may be cited as reviewed theorem-level evidence.

Status:

```text
Completed as candidate-anchor prefill. Stage100 records
PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED. It generated candidate
pages for all six Stage38 review rows and updated the Stage38 checklist with
candidate-only anchors. The claim state remains
SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED because manual
source-anchor review and native-perf evidence are still incomplete.
```

## Stage 101: CB5 Remote Native Perf Counter Evidence

Goal:

```text
Resolve the native/perf hardware-counter blocker using the authorized remote
Linux platform, while keeping theoretical-optimality wording gated.
```

Tasks:

- preserve the remote Stage28 raw logs under
  `repro/stage101_cb5_remote_native_perf/`;
- parse standard perf counters and the attribution run with retired
  load/store plus AVX512 packed floating-point counters;
- register the native Stage28 summary through
  `repro/external_evidence_intake/summary.csv`;
- keep the result as attribution evidence, not as a proof of theoretical
  optimality.

Gate:

- remote Stage28 `hardware_counter_gate` must be `PASS`;
- complete SAB target-full correctness must be `Pass`;
- retired load/store and AVX512 FP event counts must be recorded;
- one-run native timing remains attribution/smoke evidence only.

Status:

```text
Completed. Stage101 records
PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED. On native Linux with
spqlios_avx512, BINARY SET_2_3_2048, r=4, the complete SAB correctness gate
passed and the recorded speedup versus repeated scalar was 1.309x in both the
standard Stage28 run and the wider attribution counter run. CB5 is resolved as
an external-platform blocker; theoretical MAT-AVX512 optimality remains
claim-gated.
```

## Stage 102: 2025/686 Source-Anchor Review

Goal:

```text
Resolve the 2025/686 full-text review blocker by replacing Stage100
candidate-only pages with verified source anchors and explicit claim limits.
```

Tasks:

- verify protocol, complexity, correctness/noise, parameter/security,
  PVW-SAB delta, and novelty-boundary anchors;
- update `repro/stage38_fulltext_review_gate/review_checklist.csv` from
  candidate-only to reviewed source anchors;
- avoid storing full paper text in the repository.

Gate:

- the registered 2025/686 full-text artifact must remain available;
- all six Stage38 checklist rows must be
  `REVIEWED_SOURCE_ANCHORS_VERIFIED`;
- PVW/MAT statements must remain tied to local evidence, not presented as
  claims from the original 2025/686 paper.

Status:

```text
Completed. Stage102 records PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED.
CB7 is resolved for scoped theorem/protocol/citation grounding. Broad novelty
and PVW/MAT theorem claims are not upgraded by this stage.
```

## Stage 103: Related-Work And Novelty Boundary Review

Goal:

```text
Resolve the novelty-review blocker by mapping real related work to supported
and blocked contribution wording.
```

Tasks:

- record real source metadata for amortized, batch/SIMD, common-mask,
  post-686 transform, and target SAB work;
- separate supported scoped systems claims from broad claims rejected by prior
  art;
- update final audit/blocker dashboards so CB6 is resolved by scoping rather
  than by overclaiming novelty.

Gate:

- every source in `source_verification.csv` must be real and externally
  identifiable;
- broad shared-mask, batch/SIMD, new-asymptotic, all-parameter, and
  non-binary novelty claims must remain blocked unless new evidence is added;
- allowed wording must stay within the complete-SAB implementation evidence.

Status:

```text
Completed. Stage103 records
PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED. CB6 is resolved by a
scoped systems/engineering contribution boundary: the project may claim a
measured PVW/MAT-SAB implementation optimization for the 2025/686 SAB hot path,
but not broad first/shared-mask/batch/asymptotic novelty.
```

## Stage 104: Post-External Final Package Refresh

Goal:

```text
Refresh the final scoped SAB optimization package after CB5/CB6/CB7 are
resolved, without rerunning heavy benchmarks or changing scalar/default SAB.
```

Tasks:

- inherit Stage91 complete-SAB performance, correctness/noise, and resource
  evidence;
- add Stage101 native perf-counter attribution as a sample-only counter lane;
- add Stage102 reviewed 2025/686 anchors and Stage103 scoped novelty boundary;
- write a post-external final claim matrix under
  `repro/stage104_post_external_final_package/`;
- keep theoretical MAT-AVX512 optimality, broad novelty, all-parameter,
  non-binary, and default-path promotion blocked.

Gate:

- final audit A9 must be
  `SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED`;
- Stage101, Stage102, and Stage103 decision gates must pass;
- Stage91 performance/noise/resource gates must remain passing;
- Stage42 closure must be regenerated after Stage104 artifacts are added.

Status:

```text
Completed. Stage104 records
PASS_STAGE104_POST_EXTERNAL_FINAL_PACKAGE_REFRESHED_SCOPED. It is the current
post-external final package for scoped systems/engineering wording. It does not
replace Stage36/Stage88 performance statistics with the one-run Stage101 native
counter sample.
```

## Stage 105: Goal Completion Audit

Goal:

```text
Audit the active PVW/MAT-SAB objective requirement by requirement and decide
whether the scoped systems/engineering SAB acceleration evidence chain is
complete.
```

Tasks:

- map scalar/default isolation, Stage20 active-buffer fusion, complete-SAB
  performance, correctness/noise, resource, native counters, source anchors,
  novelty boundary, final package, and repro pack requirements to direct
  evidence;
- separate proven scoped evidence from stronger blocked claims;
- write the completion matrix under `repro/stage105_goal_completion_audit/`.

Gate:

- every scoped requirement must be `PROVEN_SCOPED_COMPLETE`;
- Stage104 and Stage42 verifier evidence must pass;
- broad novelty, theoretical optimality, all-parameter, non-binary, and
  default-path claims must remain blocked unless separate evidence exists.

Status:

```text
Completed. Stage105 records
PASS_STAGE105_SCOPED_GOAL_COMPLETE_STRONGER_CLAIMS_BLOCKED. The scoped
PVW/MAT-SAB systems/engineering evidence chain is complete and auditable under
its stated claim limits.
```

## Stage 106: MAT-RLWE SAB Research-Loop Reset

Goal:

```text
Reframe PVW/MAT-SAB as an r-body MAT-RLWE SAB algorithmic research program
with primary endpoint T_complete_bootstrap(r)/r, rather than as only an
engineering speedup over scalar SAB.
```

Tasks:

- define the equal-work comparison: repeated scalar SAB for `r` independent
  lanes versus one MAT-RLWE SAB call producing `r` lanes;
- reinterpret Stage36 and Stage88 evidence as amortized per-lane evidence;
- write the theory model for `T_scalar_repeat(r)`, `T_mat(r)`, and the
  lower-bound gap `A_impl(r)/A_lower_bound(r)`;
- create candidate variants for body-linear MAT external product, DFT-lazy
  schedule windows, body-major coefficient-blocked layout, and r-adaptive
  tiling;
- record strict stop rules so theory discussion must lead to a runnable
  microbench or complete-SAB gate.

Gate:

- every future speedup table must include both total latency and `T_total/r`;
- theoretical optimality remains `OPEN_NOT_PROVEN` until lower-bound gap,
  assembly/counter attribution, correctness/noise/resource, and complete-SAB
  statistics are all recorded;
- no future stage may compare one MAT run against a single scalar lane when
  the MAT run produces `r` lanes.

Status:

```text
Completed as a research-loop reset. Stage106 records
PASS_STAGE106_RESEARCH_LOOP_FIXED_OPTIMALITY_OPEN. Existing r=2/r=4 Stage36
speedups are valid amortized complete-SAB evidence, the r=6 H14 path remains a
candidate, and MAT-RLWE SAB theoretical optimality is explicitly open.
```

## Stage 107: MAT Kernel Structure Audit

Goal:

```text
Ground the next MAT-RLWE SAB step in the current source implementation and
select a runnable gate instead of continuing theory-only discussion.
```

Tasks:

- audit `src/mosfhet/src/mattrgsw.c` for generic, r=2, r=4, r=6, and r=8 MAT
  external-product paths;
- compute the source-level row/output term shape for k=1,l=1;
- decide whether current AVX512 kernels are body-linear or dense row-output;
- select the first runnable Stage108 gate.

Gate:

- if current kernels remain dense `(r+1)^2`, do not treat them as theoretical
  optimality evidence;
- select a next gate with explicit correctness, performance, and stop rules.

Status:

```text
Completed. Stage107 records
PASS_STAGE107_DENSE_KERNEL_AUDIT_NEXT_GATE_SELECTED. Current MAT kernels are
AVX512-specialized/tiled but still dense row-output accumulations. Stage108
should start with V106-D layout/locality as the first runnable gate, while
V106-B body-linear external product remains the theory-dependent optimality
path.
```

## Stage 108: V106-D Body-Major Layout Gate

Goal:

```text
Run a bounded, implementation-backed layout/locality experiment for r=6 MAT
external product before attempting any body-linear MAT-RLWE SAB optimality
claim.
```

Theory basis:

Stage107 shows the current MAT kernels are dense row-output accumulations. A
layout-only path cannot change the asymptotic `(r+1)^2` encrypted
row-output product count, but it can test whether coefficient/body traversal
order is a practical limiter for r>4. This is the correct finite gate for
V106-D because it does not change selector/key semantics.

Tasks:

- add `MAT_TRGSW_AVX512_R6_BODYMAJOR=true` as an explicit build flag;
- implement an r=6, `k=1`, `l=1` body-major AVX512 MAT external-product path;
- compare against the existing tile4 and fulltile r>4 kernels under the same
  harness;
- record correctness, kernel timing, promotion decision, and repro artifacts.

Gate:

- tile4, fulltile, and bodymajor must all pass the r>4 kernel identity gate;
- bodymajor is performance-positive only if it beats both tile4 and fulltile
  for r=6 kernel timing;
- complete-SAB promotion still requires positive `T_total/r` evidence,
  correctness/noise, and resource gates.

Status:

```text
Completed. Stage108 records
PASS_STAGE108_BODYMAJOR_NEGATIVE_NOT_PROMOTED. The body-major r=6 kernel is
correct, but it does not beat both existing r=6 layouts: for r=6 full-output
it is 1.223x faster than tile4 but 0.922x versus fulltile, and for r=6
DFT-output it is 0.935x versus tile4 and 0.937x versus fulltile. The optional
complete-SAB smoke was skipped because the kernel gate was not positive enough
to justify promotion. Do not continue blind body-major tuning; route the next
step to V106-B selector/key invariant analysis or counter-backed explanation.
```

## Stage 109: V106-B Body-Linear Invariant Gate

Goal:

```text
Decide whether body-linear MAT external product can be implemented as a local
kernel loop rewrite under the current MAT_TRGSW_DFT selector/key format.
```

Theory basis:

The current MAT external product for `k=1,l=1` has `(r+1)^2` encrypted
row-output products. A body-linear SAB optimum would need a product shape
closer to `O(r)`, but skipping encrypted off-lane terms is only valid if the
selector/key format carries a proof that those terms are redundant zero
encryptions for every output phase.

Tasks:

- extract source-level invariants for `PVW_TMLWE`, `MAT_TRGSW` rows,
  gadget injection, decomposition order, and external-product loops;
- write the dense operation model for r=1/2/4/6/8;
- decide whether V106-B is ready for a correctness harness or blocked by
  selector/key semantics.

Gate:

- if source invariants cannot be extracted, stop and update the extractor;
- if current selector rows are full PVW encryptions without skip metadata,
  block loop-only body-linear implementation;
- if not blocked, the next step must be an r=2 equivalence harness before
  any AVX512 work.

Status:

```text
Completed. Stage109 records
PASS_STAGE109_BODY_LINEAR_BLOCKED_CURRENT_SELECTOR_FORMAT. The current
MAT_TRGSW_DFT format stores full PVW_TMLWE_DFT rows with diagonal gadget
injection but no metadata/proof that off-lane encrypted-zero terms can be
skipped. The operation model confirms dense products 4/9/25/49/81 for
r=1/2/4/6/8. V106-B remains the right theoretical route, but it requires a
new selector/key-format design gate before implementation.
```

## Stage 110: r=6 Fulltile Complete-SAB Gate

Goal:

```text
Check whether the r=6 fulltile kernel advantage observed in Stage108 transfers
to complete SAB `T_total/r` under active-buffer PVW/MAT-SAB.
```

Theory basis:

Stage108 showed fulltile is the best r=6 kernel among tile4/fulltile/body-major
for the measured full-output external product. A kernel win is not enough for
SAB acceleration, so Stage110 runs complete-SAB A/B before any promotion.

Tasks:

- run r=6 tile4 and fulltile complete-SAB smoke under the same backend and
  active-buffer path;
- require full-output correctness for both variants;
- compare total PVW latency and per-lane latency;
- treat a one-run win only as a candidate.

Gate:

- correctness must pass for both variants;
- promotion requires at least 3 repeated runs plus noise/resource review;
- a one-run positive result is only a routing signal.

Status:

```text
Completed as a one-run complete-SAB smoke. Stage110 records
PASS_STAGE110_R6_FULLTILE_ONERUN_CANDIDATE_NOT_PROMOTED. Both variants passed
correctness. tile4 took 42,492,394 us total and 7,082,065.667 us/lane; fulltile
took 41,410,757 us total and 6,901,792.833 us/lane. The fulltile/tile4 ratio
is 1.026x for total and per-lane latency. This justifies a future 3+ run gate
but does not promote fulltile by itself.
```

## Stage 111: r=6 Fulltile Repeated Gate

Goal:

```text
Confirm or reject the Stage110 one-run r=6 fulltile complete-SAB signal with
at least three repeated complete-SAB runs for tile4 and fulltile.
```

Theory basis:

Stage110's fulltile signal is too small and based on one run. Since the primary
endpoint is `T_total/r`, the repeated gate must compare the PVW total/per-lane
time of the two variants directly under the same backend and active-buffer
path. A higher speedup versus repeated scalar is not enough if the scalar
baseline differs between sequential runs.

Tasks:

- run tile4 and fulltile r=6 complete-SAB benchmark for three process runs;
- require full-output correctness for every run;
- report mean, standard deviation, min, max, total latency ratio, and per-lane
  latency ratio;
- preserve raw logs as repro evidence.

Gate:

- correctness must pass for all runs;
- at least three runs are required;
- fulltile can only continue to noise/resource if its repeated PVW mean beats
  tile4 by a practical margin;
- otherwise keep it as an ablation and do not promote.

Status:

```text
Completed. Stage111 records
PASS_STAGE111_R6_FULLTILE_REPEATED_NEGATIVE_NOT_PROMOTED. All six complete-SAB
runs passed correctness. tile4 averaged 42,219,780.667 us total and
7,036,630.111 us/lane. fulltile averaged 43,336,939.000 us total and
7,222,823.167 us/lane. The repeated fulltile/tile4 PVW ratio is 0.974x, so the
Stage110 one-run signal does not survive repetition. Do not promote fulltile.
```

## Stage 112: Selector/Key-Format Gate

Goal:

```text
Turn the Stage109 current-format blocker into a concrete selector/key-format
design gate for body-linear MAT external product.
```

Theory basis:

With a shared-mask PVW accumulator, a selector row that contributes to the
output mask affects every lane phase. Even if a row has zero plaintext message
for an off-lane body, the body ciphertext component is needed to cancel the
shared mask contribution for that lane. Therefore loop-only off-lane skipping
is not valid under the current `MAT_TRGSW_DFT` format.

Tasks:

- write a concrete phase counterexample for dropping off-lane body terms while
  keeping the shared mask contribution;
- classify selector/key-format candidates for body-linear external product;
- select a finite r=2 simulator gate for any still-viable new-format route.

Gate:

- if the counterexample exists, reject current-format loop-only body-linear
  skipping;
- route only new ciphertext/key-format candidates to future implementation;
- do not reopen dense r=6 layout tuning without profile-backed evidence.

Status:

```text
Completed. Stage112 records
PASS_STAGE112_SELECTOR_FORMAT_GATE_NEW_FORMAT_REQUIRED. In the counterexample,
dense shared-mask row-output terms preserve phases `(22, 0)`, while dropping
the off-lane body term leaves phase `(22, -70)`. Candidate S112-B
loop-only-drop-offlane is rejected. Candidate S112-D lane-local-multimask and
S112-E proof-carrying-mask-partition remain design routes, but both require a
finite r=2 algebraic simulator before C implementation.
```

## Stage 113: r=2 Selector Simulator

Goal:

```text
Run the finite r=2 algebraic simulator required by Stage112 for the
lane-local multimask body-linear selector-format candidate.
```

Theory basis:

Stage112 rejects current-format loop-only off-lane skipping. A possible escape
route is to change the ciphertext/key format so each lane has local mask
accumulation. If a row used for lane 0 no longer contributes to lane 1's mask,
then off-lane body cancellation is not required for that row. This must first
be checked at phase level before any resource or C implementation work.

Tasks:

- simulate r=2 dense shared-mask reference phases;
- simulate current-format loop-only off-lane dropping as a counterexample;
- simulate lane-local multimask phases;
- record arithmetic product-count model and warnings.

Gate:

- dense reference must match expected phases;
- current-format loop-only skip must fail;
- lane-local multimask must match dense phases;
- success only permits resource/key-size modeling, not performance claims.

Status:

```text
Completed. Stage113 records
PASS_STAGE113_R2_LANE_LOCAL_SIM_PHASE_EQUIV_RESOURCE_REQUIRED. Dense reference
phases are `(73, 121)`, current-format loop-only skipping fails with
`(-362, -224)`, and the lane-local multimask candidate matches `(73, 121)`.
For r=2, the arithmetic product model is dense 9 products versus lane-local
target 5 products, a raw 1.8x product-count ratio. This is only phase and
arithmetic evidence; Stage114 must quantify key/ciphertext/noise/resource cost.
```

## Stage 114: Lane-Local Resource Model

Goal:

```text
Screen whether the Stage113 lane-local multimask candidate is immediately
killed by symbolic accumulator/key-format resource overhead.
```

Theory basis:

The current k=1 PVW accumulator has `1+r` polynomial components. A lane-local
multimask representation has roughly `2r` accumulator components. The current
dense external product has `(1+r)^2` product terms, while the lane-local
body-linear target has `1+2r` terms. This symbolic comparison must be positive
before any toy C representation is worth building.

Tasks:

- compute accumulator polynomial ratios for r=2/4/6/8;
- compute dense versus lane-local product-count ratios;
- compute a coarse product-over-accumulator screening ratio;
- preserve the warning that this is not measured RSS or complete-SAB timing.

Gate:

- if the coarse ratio is below 1, stop the lane-local branch;
- if not fatal, proceed only to a toy representation/resource measurement
  gate, not hot-path integration.

Status:

```text
Completed. Stage114 records
PASS_STAGE114_RESOURCE_MODEL_NOT_FATAL_TOY_C_REQUIRED. Lane-local accumulator
polynomial ratios for r=2/4/6/8 are 1.333/1.600/1.714/1.778, while raw product
ratios are 1.800/2.778/3.769/4.765. The minimum coarse product-over-accumulator
ratio is 1.350 at r=2. The branch is not immediately killed, but Stage115 must
measure a toy representation before implementation.
```

## Stage 115: Lane-Local Toy C Representation Gate

Goal:

```text
Measure whether the lane-local multimask representation is resource-feasible
in a concrete C layout model before implementing any MOSFHET hot-path code.
```

Theory basis:

Stage113 makes lane-local multimask phase-plausible in toy algebra and
Stage114 says the symbolic resource model is not immediately fatal. The next
valid step must therefore be executable representation evidence, not another
theory-only discussion. The measured endpoint is layout/requested bytes and RSS
for current dense shared-mask toy layout versus lane-local multimask toy layout.

Tasks:

- generate a standalone C layout probe under `repro/stage115_*`;
- compile it with WSL `gcc`;
- run current and lane-local layouts for r=2/4/6/8 and N=2048/4096;
- report requested bytes, RSS, touch time, product terms, and
  product-over-requested ratios;
- route only to a toy arithmetic equivalence prototype if resource overhead is
  bounded.

Gate:

- C probe must compile and run;
- all r/N rows must keep product-over-requested ratio above 1.0;
- target r=4, N=2048 requested-byte ratio must be at most 1.25;
- r=2, N=2048 worst-small-r control must be at most 1.50;
- passing does not permit SAB integration, AVX512 claims, noise claims, or
  complete-SAB speedup claims.

Status:

```text
Completed. Stage115 records
PASS_STAGE115_TOY_C_LAYOUT_FEASIBLE_PROTOTYPE_REQUIRED. The generated C probe
compiled under WSL gcc and measured current versus lane-local layouts for
r=2/4/6/8 and N=2048/4096. For the target r=4,N=2048 row, requested-byte
ratio is 1.100 while product terms fall from 25 to 9, giving a
product-over-requested ratio of 2.525. The r=2,N=2048 lower-control row has
requested-byte ratio 1.333 and product-over-requested ratio 1.350. This keeps
the branch alive only for Stage116 toy arithmetic equivalence; it is not
complete-SAB or MOSFHET hot-path evidence.
```

## Stage 116: Toy Arithmetic Equivalence Gate

Goal:

```text
Prove in a finite C arithmetic model that the lane-local compact formula
matches the dense shared-mask reference, while current-format off-lane
skipping remains rejected.
```

Theory basis:

Stage115 says the lane-local layout is not resource-fatal, but resource
feasibility is not correctness. The next finite gate must therefore compare
arithmetic phases directly. The dense reference evaluates all rows and relies
on off-lane body terms to cancel shared-mask contributions. The lane-local
candidate changes the mask invariant, so each lane may evaluate only the
shared row and its own body row.

Tasks:

- generate a standalone C arithmetic probe;
- test r=2/4/6 and N=64/256;
- compare dense shared-mask reference, lane-local compact arithmetic, and
  current-format drop-offlane negative control;
- record product terms and mismatches.

Gate:

- lane-local compact arithmetic must have zero mismatches against dense
  reference;
- current-format drop-offlane must fail as a negative control;
- dense product terms must remain above lane-local terms;
- passing only opens a selector/key-format prototype, not SAB integration.

Status:

```text
Completed. Stage116 records
PASS_STAGE116_TOY_ARITH_EQUIV_SELECTOR_PROTOTYPE_REQUIRED. The generated C
probe compiled and ran. Dense-vs-lane-local mismatches were zero for all
r=2/4/6 and N=64/256 rows. The current-format drop-offlane negative control
failed in every row, with drop failures 128/512 for r=2, 253/1009 for r=4,
and 384/1529 for r=6. The minimum dense-over-lane product ratio is 1.800.
This opens only a MOSFHET-adjacent selector/key skeleton gate; it still does
not authorize hot-path integration or complete-SAB speedup claims.
```

## Stage 117: Selector Skeleton Invariant Gate

Goal:

```text
Validate a finite `1+2r` lane-local selector/key term-map skeleton before
designing real MOSFHET-adjacent ciphertext/key structs.
```

Theory basis:

Stage116 proves the toy arithmetic invariant, but an implementation needs a
term map that is complete for every lane and contains no off-lane body terms.
This skeleton is still outside MOSFHET encryption, DFT storage, key generation,
noise analysis, and SAB integration.

Tasks:

- generate and compile a standalone C selector skeleton probe;
- instantiate r=2/4/6/8 term maps;
- check one shared term plus exactly one lane-local mask and body term per
  lane;
- check zero off-lane body terms and zero missing lane terms;
- record dense terms, skeleton terms, selector polys, accumulator polys, and
  product ratios.

Gate:

- every r row must pass skeleton invariants;
- off-lane body terms must be zero;
- missing lane terms must be zero;
- product ratios must stay above 1.0;
- passing only opens real-type design, not SAB hot-path integration.

Status:

```text
Completed. Stage117 records
PASS_STAGE117_SELECTOR_SKELETON_READY_REAL_TYPE_DESIGN_REQUIRED. The generated
C skeleton probe compiled and passed for r=2/4/6/8. Skeleton terms are
5/9/13/17, selector polys are 10/18/26/34, accumulator polys are 4/8/12/16,
and off-lane/missing terms are all zero. The next valid stage is real
MOSFHET-adjacent type/noise/key design outside the SAB hot path.
```

## Stage 118: Real-Type Design Gate

Goal:

```text
Convert the Stage117 selector skeleton into a MOSFHET-adjacent type, key, and
noise design gate without touching source hot paths.
```

Theory basis:

Current `MAT_TRGSW` stores full `PVW_TMLWE` rows, so lane-local body-linear
SAB cannot be represented by the current type. Stage118 defines a separate
real-type design: for k=1, the lane-local accumulator has `2r` polynomial
components, the conservative selector has `2(1+2r)` DFT polynomials, and the
key secret polynomial count remains `r`. Noise is explicitly recorded as
unproven and must be checked in a later object prototype.

Tasks:

- generate and compile a C type-shape probe;
- evaluate r=2/4/6/8 and N=2048/4096;
- record accumulator, selector, combined DFT byte, and key-secret ratios;
- record noise-term model and unknowns;
- route only to a real-object allocation/phase/noise prototype.

Gate:

- type-shape probe must compile;
- lane-local accumulator must be `2r`;
- selector must be `2(1+2r)`;
- key secret count must remain `r` for k=1;
- target r=4,N=2048 DFT byte ratio must be bounded;
- noise model must stay `RECORDED_NOT_PROVEN`.

Status:

```text
Completed. Stage118 records
PASS_STAGE118_REAL_TYPE_DESIGN_READY_OBJECT_PROTOTYPE_REQUIRED. The generated
C type-shape probe compiled and passed for r=2/4/6/8 and N=2048/4096. For
r=4,N=2048, the combined accumulator+selector DFT byte ratio is 0.866667,
the selector ratio is 0.720000, the accumulator ratio is 1.600000, and the
key-secret ratio is 1.000000. Noise rows are recorded as
NOISE_MODEL_RECORDED_NOT_PROVEN, so Stage119 must build a real-object
allocation/phase/noise prototype before any SAB integration.
```

## Stage 119: Shared-Term Object Semantics Gate

Goal:

```text
Check whether the Stage117/118 shared term can represent independent LUT
lanes, and refine the object route before real structs are written.
```

Theory basis:

Independent LUT/SAB lanes may have lane-dependent shared-row messages. A
single scalar shared term cannot represent those messages for all lanes. The
correct real-object route must therefore be tested against a scalar-shared
negative control and a vector-shared lane-local object candidate.

Tasks:

- generate and compile a C object-semantics probe;
- test scalar-shared negative control and vector-shared candidate for
  r=2/4/6 and N=64/256;
- require scalar-shared failures for independent lanes;
- require vector-shared noiseless phase equivalence;
- check toy noise against a digit-sum bound;
- record refined layout terms and byte ratios.

Gate:

- scalar-shared must fail as a negative control;
- vector-shared must have zero phase mismatches;
- toy noise must stay within the configured bound;
- vector-shared layout must not exceed the Stage118 conservative model;
- passing only opens real C struct prototype work outside `sab_pvw_*`.

Status:

```text
Completed. Stage119 records
PASS_STAGE119_VECTOR_SHARED_OBJECT_READY_REAL_STRUCT_PROTOTYPE_REQUIRED.
Scalar-shared is rejected: negative-control failures are
59/240/178/727/301/1205 across r=2/4/6 and N=64/256. Vector-shared has zero
phase mismatches and zero toy-noise bound violations on the same rows. The
valid object route is refined to vector-shared lane-local storage with `2r`
phase terms and `4r` selector polynomials for k=1. For r=4, vector/dense byte
ratio is 0.800000 and vector product ratio is 3.125000. Stage120 should build
real C structs and allocation/phase tests outside the SAB hot path.
```

## Stage 120: Real C Struct Phase/Noise Gate

Goal:

```text
Advance the vector-shared lane-local route from object-semantics toy model to
a standalone real C struct prototype with polynomial arrays and negacyclic
phase/noise checks.
```

Theory basis:

Stage119 selects vector-shared lane-local storage as the only viable shared-row
semantics for independent LUT lanes. Stage120 must therefore check whether
actual allocated C structs with polynomial arrays can preserve the phase
equation before DFT/conversion or SAB integration. The prototype uses signed
small coefficients and negacyclic multiplication; it is not a MOSFHET torus or
FFT implementation.

Tasks:

- generate and compile a standalone C prototype;
- allocate lane secrets and `2r` ciphertext-like vector-shared objects;
- encrypt shared/body message polynomials using negacyclic mask-secret
  products;
- check noiseless phase equality for r=2/4/6, N=32/64, seeds 0..4;
- inject bounded coefficient noise and check digit-sum noise bounds;
- record requested bytes and layout ratios.

Gate:

- generated C prototype must compile;
- every phase row must have zero noiseless mismatches;
- every noisy row must have zero bound violations;
- layout rows must preserve the vector-shared polynomial-count bound;
- passing only opens DFT/conversion prototyping outside `sab_pvw_*`.

Status:

```text
Completed. Stage120 records
PASS_STAGE120_REAL_STRUCT_PHASE_NOISE_READY_DFT_PROTOTYPE_REQUIRED. The
generated C prototype compiled and ran 30 phase/noise rows covering r=2/4/6,
N=32/64, and seeds 0..4. All rows had zero noiseless mismatches and zero
noise-bound violations; max observed noise equaled the configured bound 6.
Layout rows passed with vector/dense polynomial ratios 0.666667 for r=2,
0.533333 for r=4, and 0.428571 for r=6. The next stage is a DFT/conversion
object prototype, still outside SAB hot paths.
```

## Stage 121: Vector-Shared DFT/Conversion Gate

Goal:

```text
Advance the vector-shared real C struct route through an exact
frequency-domain conversion gate before any production FFT, external product,
or SAB hot-path integration.
```

Theory basis:

Stage120 proves coefficient-domain vector-shared phase/noise for allocated C
polynomial structs. Stage121 checks the next necessary boundary: converting
mask, body, and secret polynomials to a frequency-domain representation,
computing phase as `DFT(b) - DFT(a) * DFT(s)`, and converting back. The gate
uses an exact modular negacyclic NTT/DFT over modulus 12289 so failures are
semantic conversion failures rather than floating-point roundoff artifacts.

Tasks:

- generate and compile a standalone exact DFT/NTT C prototype;
- find valid 2N-th roots for N=32 and N=64;
- round-trip every vector-shared mask/body/secret polynomial;
- compare DFT-domain phase against coefficient-domain phase for clean and
  noisy shared/body objects;
- check digit-sum noise bounds after conversion;
- record vector-shared DFT polynomial-count ratios.

Gate:

- generated C prototype must compile;
- every root row must pass;
- every round-trip mismatch count must be zero;
- every clean and noisy phase mismatch count must be zero;
- every noise-bound violation count must be zero;
- layout rows must preserve the vector-shared DFT polynomial-count bound;
- passing only opens structured external-product arithmetic prototyping
  outside `sab_pvw_*`.

Status:

```text
Completed. Stage121 records
PASS_STAGE121_VECTOR_SHARED_DFT_CONVERSION_READY_STRUCTURED_EP_PROTOTYPE_REQUIRED.
The generated exact modular DFT prototype compiled and ran 30 conversion rows
covering r=2/4/6, N=32/64, and seeds 0..4. Root availability, polynomial
round-trip, clean phase, noisy phase, and noise-bound checks all had zero
failures. Layout rows passed with vector/dense DFT polynomial ratios 0.666667
for r=2, 0.533333 for r=4, and 0.428571 for r=6. The next valid stage is a
structured vector-shared external-product arithmetic prototype, still outside
the SAB hot path.
```

## Stage 122: Structured EP Arithmetic Gate

Goal:

```text
Advance the vector-shared route from exact conversion to structured
external-product arithmetic, still outside production FFT and SAB hot paths.
```

Theory basis:

Stage121 proves exact conversion of vector-shared objects. Stage122 checks the
next finite invariant: applying selector digit polynomials to vector-shared
objects with only two retained terms per lane must match a dense clean
reference phase that evaluates all lane/row terms. Because dense and
vector-shared masks are intentionally different, equality is required at the
decrypted phase. The gate also checks that coefficient-domain structured EP
matches exact DFT-domain structured EP, and that body-only off-lane skipping
fails as a negative control.

Tasks:

- generate and compile a standalone structured EP C prototype;
- build dense clean reference outputs over `r(r+1)` terms;
- build vector-shared structured outputs over `2r` terms;
- build the same structured outputs through exact DFT multiply-add;
- compare dense clean phase against structured clean phase;
- compare coefficient-domain structured EP against exact DFT-domain EP;
- check conservative noisy structured EP bounds;
- require body-only off-lane skip to fail as a negative control.

Gate:

- generated C prototype must compile;
- every dense/structured phase mismatch count must be zero;
- every coefficient/DFT structured EP mismatch count must be zero;
- every noisy bound violation count must be zero;
- every negative-control row must have at least one failure;
- term and selector ratios must remain above 1.0;
- passing only opens production torus/FFT smoke prototyping outside
  `sab_pvw_*`.

Status:

```text
Completed. Stage122 records
PASS_STAGE122_STRUCTURED_EP_ARITHMETIC_READY_PRODUCTION_FFT_SMOKE_REQUIRED.
The generated exact modular structured-EP prototype compiled and ran 30 rows
covering r=2/4/6, N=32/64, and seeds 0..4. Dense clean phase vs structured
phase mismatches, coefficient-vs-DFT structured mismatches, and noisy bound
violations are all zero. The body-only off-lane skip negative control fails in
every row as required. EP term ratios are 1.5x for r=2, 2.5x for r=4, and
3.5x for r=6; selector-polynomial ratios are 1.125x, 1.5625x, and 2.041667x.
The next valid stage is production torus/FFT smoke outside the SAB hot path.
```

## Stage 123: Production FFT Smoke Gate

Goal:

```text
Move the Stage122 vector-shared structured EP arithmetic across the actual
MOSFHET `TorusPolynomial` and SPQLIOS DFT API boundary, still outside
`sab_pvw_*` and without changing scalar/default SAB behavior.
```

Theory basis:

Stage122 proves structured EP arithmetic only in an exact modular prototype.
Stage123 checks the next finite boundary: the same structured EP semantics
must survive MOSFHET torus polynomial multiplication, production
`polynomial_torus_to_DFT`, `polynomial_mul_addto_DFT`, and
`polynomial_DFT_to_torus`. Because SPQLIOS is floating point, the production
DFT comparison is a smoke check with a fixed 1024 torus-unit tolerance, not a
cryptographic noise proof.

Tasks:

- build MOSFHET `libmosfhet.a` with `FFT_LIB=spqlios`;
- generate and compile a standalone structured EP smoke probe linked against
  the production MOSFHET static library;
- compare coefficient-domain structured EP phase with the dense
  message-reference phase exactly;
- compare production DFT structured EP phase with coefficient structured EP
  within the fixed tolerance;
- repeat the check with bounded added message noise;
- keep body-only off-lane skipping as a required failing negative control;
- record Stage122 term ratios at production smoke sizes.

Gate:

- MOSFHET static build must pass;
- standalone probe must compile and run;
- every coefficient-domain phase mismatch count must be zero;
- every production DFT and noisy DFT mismatch count must be zero under the
  declared tolerance;
- every body-only off-lane skip negative-control row must fail;
- layout rows must preserve structured EP term ratios above 1.0;
- passing only opens MOSFHET-adjacent type/API sketching outside the SAB hot
  path.

Status:

```text
Completed. Stage123 records
PASS_STAGE123_PRODUCTION_FFT_SMOKE_READY_MOSFHET_TYPE_SKETCH_REQUIRED. The
MOSFHET static library built with FFT_LIB=spqlios, the standalone probe linked
against libmosfhet.a, and 7 production FFT smoke rows passed for r=2/4/6 at
N=1024 plus r=2 at N=2048. Coefficient-domain structured EP mismatches are
zero, production DFT and noisy DFT mismatches are zero under the fixed 1024
torus-unit tolerance, and the maximum observed DFT gap is 619. Body-only
off-lane skip remains rejected with 2048/4096/6144 failures depending on r and
N. Term ratios remain 1.5x for r=2, 2.5x for r=4, and 3.5x for r=6. The next
valid stage is a MOSFHET-adjacent vector-shared type/API sketch; this is still
not gadget decomposition, AVX512 optimality, SAB schedule integration, or
complete `T_bootstrap/r` evidence.
```

## Stage 124: MOSFHET Type/API Skeleton Gate

Goal:

```text
Turn the Stage123 production FFT smoke result into a compile-checked
MOSFHET-adjacent vector-shared accumulator and compact selector type/API
skeleton, still outside `sab_pvw_*`.
```

Theory basis:

Stage119 rejects scalar-shared storage and selects vector-shared lane-local
objects. Stage122/123 show that structured EP arithmetic can be represented in
coefficient and production DFT domains. Stage124 checks the next implementation
boundary: the type shape must be expressible using MOSFHET-style allocation,
ownership, DFT lifecycle, and explicit lane-indexed selector accessors without
falling back to dense `MAT_TRGSW_DFT` rows.

Tasks:

- build MOSFHET `libmosfhet.a` with `FFT_LIB=spqlios`;
- generate and compile a standalone C skeleton linked against MOSFHET;
- define lane-local torus and DFT ciphertext structs with mask/body fields;
- define an r-lane vector-shared accumulator and compact selector DFT arrays
  `shared[t,q]` and `body[t,q]`;
- verify non-null, non-aliased component ownership;
- verify k/r/N/T metadata and lane-local shared/body coverage;
- verify accumulator torus->DFT->torus lifecycle under the production
  conversion tolerance;
- record current dense versus vector-shared accumulator, selector, and total
  polynomial counts.

Gate:

- build, compile, and run must pass;
- component ownership, metadata, and lane coverage failures must be zero;
- accumulator DFT roundtrip mismatches must be zero under the declared
  tolerance;
- compact selector and total accumulator+selector counts must beat current
  dense counts for the tested r/N rows;
- passing only opens compact selector gadget-decomposition prototyping outside
  the SAB hot path.

Status:

```text
Completed. Stage124 records
PASS_STAGE124_MOSFHET_TYPE_API_SKELETON_READY_GADGET_DECOMPOSITION_GATE_REQUIRED.
The generated MOSFHET-adjacent skeleton compiles and runs against
FFT_LIB=spqlios for k=1, T=7, r=2/4/6, and N=1024/2048. Component ownership,
metadata, selector lane coverage, and roundtrip mismatch counts are all zero;
the maximum production DFT roundtrip gap is 1 under the fixed 1024 torus-unit
tolerance. For r=4, the compact selector count is 112 versus current dense
175, and total accumulator+selector count is 120 versus 180. The next valid
stage is compact selector gadget decomposition and diagonal injection; this is
still not selector encryption, noise proof, AVX512 performance, SAB schedule
integration, or complete `T_bootstrap/r` evidence.
```

## Stage 125: Compact Selector Gadget-Decomposition Gate

Goal:

```text
Check whether the Stage124 compact selector skeleton can support lane-local
gadget decomposition and diagonal injection without reconstructing dense
`MAT_TRGSW_DFT` rows.
```

Theory basis:

Current dense MAT external product decomposes `k+r` accumulator components and
uses dense selector rows. The vector-shared route decomposes two lane-local
components per lane: shared-mask and body. Stage125 checks that those
decomposition streams can drive compact selector rows `shared[t,q]` and
`body[t,q]` whose diagonal gadget injection matches the coefficient reference
through production DFT.

Tasks:

- build MOSFHET `libmosfhet.a` with `FFT_LIB=spqlios`;
- generate and compile a standalone compact selector gadget probe;
- decompose lane-local mask/body polynomials using `polynomial_decompose_i`;
- inject gadget monomials into compact shared/body selector rows;
- compare coefficient-domain gadget application with production DFT
  multiply-add under the declared tolerance;
- keep body-only selector rows as a required failing negative control;
- record selector-storage ratio, decomposition-stream overhead, and
  selector+decomposition count ratio.

Gate:

- build, compile, and run must pass;
- coefficient-vs-DFT gadget mismatch counts must be zero under tolerance;
- body-only negative control must fail;
- compact selector storage ratio must remain above 1.0;
- selector+decomposition count ratio must not fall below 1.0;
- passing only opens compact selector encryption/noise prototyping outside the
  SAB hot path.

Status:

```text
Completed. Stage125 records
PASS_STAGE125_COMPACT_SELECTOR_GADGET_READY_ENCRYPTION_NOISE_GATE_REQUIRED.
The production DFT compact gadget rows pass for k=1, T=7, Bg_bit=7, r=2/4/6,
N=1024/2048, and seed subset 0..1. All coefficient-vs-DFT mismatch counts are
zero under the fixed 16384 torus-unit tolerance; the maximum observed DFT gap
is 10240. Body-only selector rows remain rejected. The layout model records
selector ratios 1.125x/1.5625x/2.041667x for r=2/4/6, but
decomposition-stream overhead makes selector+decomposition count only break
even for r=2 and positive for r=4/r=6 at 1.25x/1.555556x. The next valid
stage is compact selector encryption/noise modeling; this is still not noise
proof, AVX512 performance, SAB schedule integration, or complete
`T_bootstrap/r` evidence.
```

## Stage 126: Compact Selector Encryption/Noise Gate

Goal:

```text
Verify that compact selector rows can be represented as encrypted lane-local
mask/body ciphertexts whose external-product phase equals the clean gadget
reference plus modeled selector noise, still outside `sab_pvw_*`.
```

Theory basis:

Stage125 proves compact gadget injection with plaintext-like rows. Stage126
adds the next required invariant: compact selector rows must behave like
encrypted lane-local rows. The probe constructs deterministic ciphertext-like
rows `body = mask * secret + gadget + noise` using MOSFHET polynomial
operations, applies decomposed lane-local digits, and checks both coefficient
and production DFT external-product phases against the exact modeled noisy
reference.

Tasks:

- build MOSFHET `libmosfhet.a` with `FFT_LIB=spqlios`;
- generate and compile a deterministic compact selector encryption/noise
  probe;
- build lane-local secrets, compact selector masks, messages, and bounded
  deterministic noise;
- verify coefficient-domain phase equals clean reference plus modeled noise;
- verify production DFT external-product phase against the modeled noisy
  reference under tolerance;
- verify modeled noise stays within a declared conservative bound;
- keep body-only encrypted selector rows as a required failing negative
  control;
- record per-lane selector-noise term ratios and selector storage ratios.

Gate:

- build, compile, and run must pass;
- coefficient phase and noise model mismatch counts must be zero;
- production DFT mismatch counts must be zero under tolerance;
- modeled noise must remain within the declared bound;
- body-only encrypted selector rows must fail;
- compact per-lane noise term count and selector storage must remain below
  current dense counts;
- passing only opens isolated compact external-product kernel work outside the
  SAB hot path.

Status:

```text
Completed. Stage126 records
PASS_STAGE126_COMPACT_SELECTOR_ENCRYPTION_NOISE_READY_ISOLATED_EP_KERNEL_REQUIRED.
The deterministic encryption/noise simulator passes for k=1, T=7, Bg_bit=7,
r=2/4/6, N=512/1024, and seed subset 0..1. Coefficient phase mismatches,
production DFT mismatches, noise-model mismatches, and noise-bound violations
are all zero. The maximum production DFT gap is 14449 under tolerance 131072,
and the maximum modeled noise is 13022 under bound 917504. Body-only encrypted
selector rows remain rejected. Per-lane selector-noise term ratios are
1.5x/2.5x/3.5x for r=2/4/6, and selector-storage ratios remain
1.125x/1.5625x/2.041667x. The next valid stage is an isolated compact
external-product kernel, still outside SAB integration and complete
`T_bootstrap/r` claims.
```

## Stage 127: Isolated Compact External-Product Kernel Gate

Goal:

```text
Factor the Stage126 compact selector external product into a reusable
isolated DFT kernel with explicit scratch, while keeping production MOSFHET
headers and `sab_pvw_*` unchanged.
```

Theory basis:

Stage126 validates compact selector encryption/noise semantics, but its
external product is still inline in the generated probe. Stage127 checks the
next implementation boundary: the same operation must be expressible as a
kernel-shaped function that decomposes lane-local shared/body source
polynomials, converts digits to DFT, applies `shared[t,q]` and `body[t,q]`
selector rows, and returns lane-local DFT mask/body output.

Tasks:

- build MOSFHET `libmosfhet.a` with `FFT_LIB=spqlios`;
- generate and compile a standalone isolated compact EP kernel probe;
- define `compact_ep_kernel_dft(...)` and explicit scratch buffers;
- compare kernel DFT output components with a coefficient-domain reference;
- compare kernel phase against the modeled noisy reference;
- keep a body-only kernel as a required failing negative control;
- record dense versus compact DFT-term and decomposition-included total-term
  ratios.

Gate:

- build, compile, and run must pass;
- kernel output component mismatch counts must be zero under tolerance;
- kernel phase mismatch and noise-model mismatch counts must be zero under
  tolerance;
- body-only kernel must fail;
- compact DFT-term ratio must be above 1.0 and total-term ratio must be at
  least 1.0;
- passing only opens a MOSFHET-adjacent compact EP API boundary stage outside
  the SAB hot path.

Status:

```text
Completed. Stage127 records
PASS_STAGE127_ISOLATED_COMPACT_EP_KERNEL_READY_API_BOUNDARY_REQUIRED. The
generated `compact_ep_kernel_dft` probe passes for k=1, T=7, Bg_bit=7,
r=2/4/6, N=512/1024, and seed subset 0..1. Component, phase, and exact
noise-model mismatch counts are zero for all 9 rows. The maximum component gap
is 14645 and the maximum phase gap is 14653 under tolerance 131072. Body-only
kernel rows remain rejected. DFT-term ratios are
1.125x/1.5625x/2.041667x for r=2/4/6; total-term ratios including
decomposition are 1.0x/1.25x/1.555556x. The next valid stage is a
MOSFHET-adjacent compact EP API boundary, still outside SAB integration and
complete `T_bootstrap/r` claims.
```

## Stage 128: Compact EP API Boundary Gate

Goal:

```text
Wrap the isolated compact EP kernel in MOSFHET-adjacent selector, output, and
scratch API shapes without changing production MOSFHET headers, scalar SAB, or
`sab_pvw_*`.
```

Theory basis:

Stage127 proves a generated isolated compact EP kernel. Stage128 checks the
next implementation boundary before any hot-path integration: selector row
ownership, output ownership, explicit scratch ownership, invalid-lane guards,
and no API-owned allocation in the hot call must all preserve the same
component, phase, noise-model, negative-control, and count-model invariants.

Tasks:

- build MOSFHET `libmosfhet.a` with `FFT_LIB=spqlios`;
- generate and compile a standalone compact EP API boundary probe;
- define `CompactEpSelectorDft`, `CompactEpOutputDft`, and `CompactEpScratch`;
- verify selector/output/scratch ownership and metadata;
- verify invalid row/lane guards reject bad inputs;
- verify `compact_ep_kernel_dft_api(...)` performs no API-owned allocation in
  the measured hot call;
- compare API kernel DFT output components with the coefficient-domain
  reference;
- compare API kernel phases against the modeled noisy reference;
- keep a body-only API kernel as a required failing negative control;
- preserve the Stage127 DFT-term and decomposition-included count model.

Gate:

- build, compile, and run must pass;
- ownership, metadata, guard, and hot-kernel allocation failure counts must be
  zero;
- component, phase, and noise-model mismatch counts must be zero under the
  declared tolerance;
- body-only API kernel must fail;
- DFT-term ratio must stay above 1.0 and total ratio must stay at least 1.0;
- passing only opens isolated microbench/profiling and production API design,
  not SAB integration or complete `T_bootstrap/r` claims.

Status:

```text
Completed. Stage128 records
PASS_STAGE128_COMPACT_EP_API_BOUNDARY_READY_MICROBENCH_REQUIRED. The generated
API-boundary probe passes for k=1, T=7, Bg_bit=7, r=2/4/6, N=512/1024, and
seed subset 0..1. Ownership, metadata, invalid-guard, hot-kernel allocation,
component, phase, and exact noise-model mismatch counts are all zero. The
maximum component gap is 14605 and maximum phase gap is 14608 under tolerance
131072. Body-only API kernel rows remain rejected. DFT-term ratios are
1.125x/1.5625x/2.041667x for r=2/4/6; total ratios including decomposition
are 1.0x/1.25x/1.555556x. The next valid stage is isolated compact EP
microbench/profiling and assembly/perf-counter attribution, still outside SAB
integration and complete `T_bootstrap/r` claims.
```

## Stage 129: Compact EP Isolated Microbench Gate

Goal:

```text
Measure whether the Stage128 API-shaped compact EP kernel preserves its count
advantage as wall-clock time before production header work or SAB integration.
```

Theory basis:

Stage128 proves the API boundary semantically. Stage129 checks timing under the
same MOSFHET/SPQLIOS primitive boundary by comparing an all-lane compact kernel
against a dense-count proxy and separating full kernel time from
decomposition/DFT-only and DFT-addmul-only time. The dense proxy is not a full
SAB or production key-format benchmark; it is a cost proxy for current dense
`T*(k+r)^2` DFT multiply-add work.

Tasks:

- replay Stage128 API correctness rows before timing;
- benchmark `dense_all_proxy` versus `compact_all_lanes` for r=2/4/6 and
  N=512/1024;
- benchmark `dense_decomp_dft_proxy` versus `compact_decomp_dft`;
- benchmark `dense_addmul_proxy` versus `compact_addmul`;
- report mean timing over five samples, six reps per sample;
- decide promote/neutral strictly from r=4/r=6 full-kernel timing.

Gate:

- build, compile, run, API correctness replay, and benchmark row generation
  must pass;
- promotion toward production API requires compact all-lane timing to beat the
  dense-count proxy for both r=4 and r=6;
- if addmul is positive but full timing is not, do not promote; instead target
  decomposition/DFT reuse or streaming.

Status:

```text
Completed as neutral. Stage129 records
NEUTRAL_STAGE129_COMPACT_EP_MICROBENCH_NOT_PROMOTED. Build, compile, run, API
correctness replay, and benchmark row generation pass. The full compact
all-lane signal is negative for r=4: speedup is 0.925687 at N=512 and 0.888032
at N=1024. r=6 is positive at 1.063672 and 1.109918. Attribution shows compact
DFT addmul is positive for r=4/r=6 (1.369610-1.867126), but compact
decomposition/DFT is slower (0.580632-0.619392 for r=4/r=6). The next valid
stage is a decompose/DFT reuse or streaming gate, not production API or SAB
integration.
```

## Stage 130: Shared-Source Compact EP Gate

Goal:

```text
Test the MAT-RLWE source shape with one shared source/mask polynomial and r
body polynomials, while keeping lane-local compact selector rows.
```

Theory basis:

Stage129 shows the compact DFT addmul path is positive but the vector-shared
`2r` decomposition/DFT streams block r=4. The original MAT-RLWE target is
closer to one shared mask/source plus r bodies. Stage130 therefore checks the
finite phase/noise invariant and timing for the shared-source shape before any
production header or SAB integration.

Tasks:

- implement a generated shared-source compact EP probe outside production
  MOSFHET headers;
- verify component, phase, and exact noise-model equivalence for r=2/4/6 and
  N=512/1024;
- keep body-only shared-source output as a required failing negative control;
- benchmark dense-count proxy versus shared-source compact all-lane output;
- separately benchmark decomposition/DFT and DFT addmul attribution;
- promote only toward production API design, not SAB integration.

Gate:

- build, compile, run, correctness, negative control, and benchmark rows must
  pass;
- r=4 and r=6 full microbench must both beat the dense-count proxy;
- any positive result remains isolated EP evidence until production API,
  SAB integration, correctness/noise, and full `T_bootstrap/r` gates pass.

Status:

```text
Completed positive. Stage130 records
PASS_STAGE130_SHARED_SOURCE_COMPACT_EP_POSITIVE_PRODUCTION_API_REQUIRED.
Component, phase, and exact noise-model mismatch counts are zero for 6 tested
rows, with max component/phase gaps 13697/13703 under tolerance 131072.
Body-only negative controls are rejected. Full microbench speedups are
1.281272/1.153336 for r=4 at N=512/1024 and 1.478479/1.369582 for r=6 at
N=512/1024. r=2 remains negative/near break-even at 0.990025/0.967843. The
next valid stage is a production API/header design gate for shared-source
compact EP, still outside SAB integration.
```

## Stage 131: Shared-Source Production API Gate

Goal:

```text
Move the Stage130 shared-source compact EP shape from generated probe code into
MOSFHET public headers and `mattrgsw.c`, without changing scalar SAB or the
existing dense MAT path.
```

Theory basis:

Stage130 proves isolated component/phase/noise semantics and positive r=4/r=6
microbench for the shared-source shape. Stage131 checks the next software
boundary: the API must compile through `mosfhet.h`, link through
`libmosfhet.a`, and preserve the same semantic invariant. The output remains
one mask/body pair per lane (`MAT_TRGSW_COMPACT_OUTPUT_DFT`); it is not yet a
true `PVW_TMLWE_DFT` with a single shared output mask.

Tasks:

- add `MAT_TRGSW_COMPACT_DFT`, `MAT_TRGSW_COMPACT_OUTPUT_DFT`, and
  `MAT_TRGSW_COMPACT_MUL_SCRATCH` to `mosfhet.h`;
- add alloc/free/set-row/kernel functions in `mattrgsw.c`;
- build MOSFHET static library with `ENABLE_PVW_TMLWE=true`;
- compile an external probe against the public header and static library;
- verify component, phase, exact noise-model, invalid-row guards, and
  body-only negative controls for r=2/4/6 and N=512/1024.

Gate:

- build, public-header compile/link, and run must pass;
- guard, component, phase, and noise-model mismatch counts must be zero;
- body-only negative controls must fail;
- passing only opens SAB integration design around this output type.

Status:

```text
Completed. Stage131 records
PASS_STAGE131_SHARED_SOURCE_PRODUCTION_API_READY_SAB_INTEGRATION_DESIGN. The
public API probe passes for k=1, T=7, Bg_bit=7, r=2/4/6, and N=512/1024.
Guard, component, phase, and exact noise-model mismatch counts are zero for all
6 rows. Body-only negative controls are rejected. The maximum component/phase
gaps are 13481/13475 under tolerance 131072. The next valid stage is isolated
SAB CMUX/RGSW integration design using `MAT_TRGSW_COMPACT_OUTPUT_DFT`; complete
`T_bootstrap/r` claims remain blocked.
```

## Stage 132: Lane-Pair CMUX Delta Consumption Gate

Goal:

```text
Validate that the Stage131 lane-pair compact EP output can be consumed by an
isolated CMUX delta update `base + EP(in2 - in1)` without converting it into a
false shared-output-mask PVW ciphertext.
```

Theory basis:

The Stage131 output is one mask/body pair per lane. A standard `PVW_TMLWE_DFT`
has one shared mask and r bodies, so treating the Stage131 output as standard
PVW would be an invalid invariant unless separately proven. Stage132 therefore
checks the exact per-lane phase/noise consumer equation and keeps a negative
control that collapses all masks to lane 0.

Gate:

- public API build/compile/run must pass;
- component, delta-phase, consumer-phase, and noise-model mismatches must be
  zero for r=2/4/6 and N=512/1024;
- the shared-output-mask collapse negative control must fail for r>1;
- passing opens only lane-state RGSW/sparse schedule design.

Status:

```text
Completed. Stage132 records
PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED.
The deterministic public-API probe passes for k=1, T=7, Bg_bit=7, r=2/4/6,
and N=512/1024. Component, delta-phase, consumer-phase, and exact noise-model
mismatch counts are zero. Collapsing lane-pair masks into one shared output
mask fails as required. The next valid step is a compact lane-state
accumulator object for RGSW monomial and sparse schedule integration.
```

## Stage 133: Lane-State Closure Audit

Goal:

```text
Determine whether the Stage131 shared-source compact EP can be directly
iterated after Stage132 CMUX consumption, or whether a different state/input
kernel is required.
```

Theory basis:

Stage131 consumes one shared source mask and r bodies. Stage132 validates an
output with one mask/body pair per lane and rejects collapse to one shared
output mask. Therefore a repeated SAB schedule cannot feed the post-CMUX
lane-pair accumulator back into the Stage131 shared-source kernel without a new
invariant or conversion.

Status:

```text
Completed. Stage133 records
PASS_STAGE133_CLOSURE_AUDIT_DIRECT_SHARED_SOURCE_ITERATION_BLOCKED. Lane-pair
state is valid as an internal accumulator representation, but direct
Stage131 shared-source compact EP iteration is blocked by state shape. The
primary next route is a generalized lane-pair input compact EP correctness and
microbench gate.
```

## Stage 134: Generalized Lane-Pair Input EP Gate

Goal:

```text
Replay and validate the closure-capable generalized lane-pair input compact EP
path selected by Stage133, including correctness and same-backend microbench.
```

Status:

```text
Completed. Stage134 records NEUTRAL_STAGE134_GENERALIZED_INPUT_EP_CORRECT_BUT_PERF_BLOCKED. Correctness rows pass for r=2/4/6 and
N=512/1024. The full-kernel timing signal has min r=4/r=6 speedup
0.910791 and max all-row speedup 1.101122. This stage decides only
isolated EP closure/performance readiness; complete SAB claims remain blocked.
```

## Stage 135: Decompose/DFT Reuse Target Gate

Goal:

```text
Turn Stage134's neutral closure-capable EP result into concrete decompose/DFT
optimization targets before any RGSW/sparse integration.
```

Status:

```text
Completed. Stage135 records PASS_STAGE135_DECOMP_DFT_REUSE_TARGETS_READY_STAGE136. For r=4, the required decompose/DFT
speedup is 1.152711 for break-even and 1.245156 for a
5pct full-kernel gain. The next valid stage is a decompose/DFT reuse or
batching implementation gate.
```

## Stage 136: Batched Decompose/DFT Gate

Goal:

```text
Prototype exact batched decompose-to-DFT for generalized lane-pair input and
check whether it meets the Stage135 r=4 target.
```

Status:

```text
Completed. Stage136 records FAIL_STAGE136_BATCHED_DECOMP_DFT_GATE. The minimum r=4 batched/current
decompose-DFT speedup is . This is a microbench-only result and does
not prove full EP, RGSW, sparse schedule, or complete `T_bootstrap/r`.
```

## Stage 137: Decompose/DFT Attribution Gate

Goal:

```text
Split generalized lane-pair input decompose/DFT timing into decompose-only and
DFT-only parts after Stage136 rejected simple batched decomposition.
```

Status:

```text
Completed. Stage137 records PASS_STAGE137_DFT_CONVERSION_DOMINANT_READY_DFT_ROUTE. For r=4, minimum DFT fraction is
0.862257 and maximum required DFT-only speedup is 1.340453. This is an
attribution gate only, not full EP or SAB acceleration.
```

## Stage 138: Shared-Mask Compact MAT Gate

Goal:

```text
Validate the true MAT-RLWE interpretation: one shared mask and r body lanes,
measured as amortized external-product time per lane.
```

Status:

```text
Completed. Stage138 records PASS_STAGE138_SHARED_MASK_COMPACT_PROMOTED_READY_SAB_INTEGRATION. For r=4, per-bit kernel speedup is
1.293981-1.491182. This remains a kernel gate; full SAB claims are still
blocked until compact selectors are integrated into CMUX/RGSW/sparse_mul.
```

## Stage 139: Compact Closure Audit

Goal:

```text
Determine whether Stage138 diagonal compact output is directly usable as a
PVW_TMLWE SAB state with one shared mask and r bodies.
```

Status:

```text
Completed. Stage139 records PASS_STAGE139_COMPACT_DIAGONAL_NOT_PVW_CLOSED_REDIRECT_FULL_MAT_ROUTE. Minimum mask mismatch count is
512.000000; direct diagonal compact SAB integration is blocked. Stage140
must use full MAT PVW_TMLWE output or design a shared-output compact kernel.
```

## Stage 140: Closed Full-MAT Attribution Gate

Goal:

```text
Attribute the production closed full-MAT external product after Stage139 blocks
direct diagonal compact SAB integration.
```

Status:

```text
Completed. Stage140 records PASS_STAGE140_CLOSED_FULLMAT_DFT_COUNT_LOWER_BOUND_READY_STAGE141. The closed input DFT count is already
at `(r+1)T`; for target-shape r=4,T=1 the minimum addmul fraction is
0.546981 and minimum decomp/DFT fraction is 0.445453. Stage141
must optimize the dominant closed component, not the invalid diagonal output.
```

## Stage 141: AVX512 Closed Full-MAT Target Gate

Goal:

```text
Compare generic, small-r, and r4-unrolled AVX512 closed full-MAT kernels under
the same `spqlios_avx512` backend for target shape r=4,T=1.
```

Status:

```text
Completed. Stage141 records FAIL_STAGE141_AVX512_CLOSED_FULLMAT_GATE. r4-unrolled versus generic speedup is
1.093355-1.373156 across N=1024/2048, but the specialized kernels fail
Torus-level equivalence for r=4. This is a correctness blocker; Stage142 must
debug or reject the AVX512 small-r/r4-unrolled kernels before any complete SAB
A/B run can use these flags.
```
## Stage 142: AVX512 FMA-Order Fix Gate

Goal:

```text
Repair the Stage141 specialized-kernel correctness blocker by matching the
generic AVX512 FMA order in MAT-aware complex addmul, then rerun the closed
full-MAT r=4 target kernel gate.
```

Status:

```text
Completed. Stage142 records PASS_STAGE142_AVX512_FMA_ORDER_FIX_PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN. The r4-unrolled closed full-MAT mean
kernel speedup over generic AVX512 is 1.176373-1.267909 for r=4,T=1,N=1024/2048.
This is a kernel-only result; Stage143 must run complete SAB A/B with
T_bootstrap/r as the primary endpoint.
```
## Stage 143: Full SAB r4-Unrolled Smoke

Goal:

```text
Move from Stage142 kernel-only promotion to a complete SAB smoke using the
amortized endpoint T_bootstrap/r.
```

Status:

```text
Completed. Stage143 records SMOKE_STAGE143_FULL_SAB_R4_UNROLLED_POSITIVE_REPEATED_REQUIRED. r4-unrolled active-buffer full SAB
has per-lane PVW time 7125020.500 us versus generic active
7586131.750 us, incremental smoke speedup
1.064717. Against repeated scalar SAB, the
r4-unrolled smoke speedup is 1.355000x. Repeated
Stage144 is required before a final bootstrapping claim.
```
## Stage 144: Full SAB Repeated r4-Unrolled Gate

Goal:

```text
Promote Stage143 from one-run smoke to repeated complete-SAB A/B with
correctness, final-output noise, and resource evidence for the explicit
r4-unrolled AVX512 candidate.
```

Status:

```text
Completed. Stage144 records WEAK_STAGE144_R4_UNROLLED_POSITIVE_STATS_REVIEW_REQUIRED. The primary endpoint is
T_bootstrap/r. r4-unrolled versus generic active PVW has mean paired speedup
1.000249, min 0.924113,
and CI95 [0.835834, 1.164664].
Noise status is PASS across 3 seeds. Resource
key/RSS ratios are 1.065349 and 0.997049.
```
## Stage 145: r4-Unrolled Promotion-Policy Audit

Goal:

```text
Convert Stage144 evidence into an explicit keep/promote/reject policy without
overstating the full-SAB result.
```

Status:

```text
Completed. Stage145 records WEAK_STAGE145_POLICY_KEEP_EXPLICIT_DO_NOT_PROMOTE. Default behavior remains
unchanged. Claim policy is DISALLOW_FINAL_SPEEDUP_CLAIM_ALLOW_NEGATIVE_ABLATION. Next action:
Stage146 should attribute variance or route to another algorithmic candidate.
```
## Stage 146: r4-Unrolled Variance Attribution

Goal:

```text
Explain the Stage144 weak repeated result and decide whether r4-unrolled AVX512
deserves more full-SAB work or should remain only an explicit ablation.
```

Status:

```text
Completed. Stage146 records PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT. It consumes Stage144 repeated
rows, runs one body-profile diagnostic pair, and keeps scalar/default behavior
unchanged.
```
## Stage 147: H14 r=6 Current-Head Route

Goal:

```text
After the r4-unrolled branch remains explicit-only, verify whether the
previously preferred H14 backend FromDFT-add r=6 path is still the right
current-head candidate branch.
```

Status:

```text
Completed. Stage147 records PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT. It runs a current-head wrapper/backend
r=6 full-SAB profile smoke and preserves scalar/default behavior.
```
## Stage 148: H14 r=6 Repeated Refresh

Goal:

```text
Upgrade the Stage147 current-head H14 r=6 backend smoke into repeated
complete-SAB performance, final-output noise, and resource evidence.
```

Status:

```text
Completed. Stage148 records PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE. It preserves scalar/default behavior
and keeps the endpoint at amortized `T_bootstrap/r`.
```
## Stage 149: H14 r=6 Claim Policy

Goal:

```text
Convert Stage148 repeated/noise/resource evidence into a bounded claim policy
without changing defaults or overclaiming novelty.
```

Status:

```text
Completed. Stage149 records PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT. It allows scoped explicit-path
engineering wording only; default-path and paper-level novelty claims remain
disallowed.
```
## Stage 150: Final Package Refresh

Goal:

```text
Refresh the final package around the MAT-RLWE/PVW-SAB amortized endpoint
T_complete_bootstrap(r)/r and the Stage148/149 explicit H14 r=6 evidence.
```

Status:

```text
Completed. Stage150 records PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED. The current allowed claim is scoped to
the explicit H14 r=6 backend path. It reports backend-versus-repeated-scalar
speedup 1.432667 under
T_bootstrap/r, key bytes ratio 1.122537, and
VmHWM ratio 1.030966. Default-path, all-parameter,
novelty, and theoretical-optimality claims remain blocked.
```
## Stage 151: H14 r=6 Fulltile Backend Smoke

Goal:

```text
Test whether composing the Stage148 H14 backend FromDFT-add route with the
r=6 fulltile MAT external-product layout improves complete SAB T_bootstrap/r.
```

Status:

```text
Completed. Stage151 records WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL. The timing smoke value is
1.002631;1.013780 for `T_bootstrap/r;mat_ep`. This is routing evidence
only; default-path and final-paper claims remain blocked.
```
## Stage 152: Dual-Sub Kernel Gate

Goal:

```text
Test H14-C3 shared-input dual subtraction as an isolated kernel before any
complete-SAB integration.
```

Status:

```text
Completed. Stage152 records PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE. Isolated local speedup is
1.150215 mean / 1.122825 min and predicted r=6 body speedup is
1.020287. This is not a complete SAB claim.
```
## Stage 153: Dual-Sub Full-SAB Gate

Goal:

```text
Integrate the Stage152 shared-input dual-sub kernel behind an explicit flag and
test complete SAB `T_bootstrap/r` against the same H14 r=6 backend control.
```

Status:

```text
Completed. Stage153 records NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED. The full-SAB smoke dual/control
speedup on `T_bootstrap/r` is 1.002283. Dynamic pair calls are
5080/5080, and the corrected body-level
bound is 1.000352. The key conclusion is that H14-C3 is pair-fraction limited.
```
## Stage 154: Bodymajor Full-SAB Closeout

Goal:

```text
Close the skipped Stage108 complete-SAB gate for r=6 bodymajor layout under
the current H14 backend FromDFT-add path.
```

Status:

```text
Completed. Stage154 records REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER. Bodymajor/tile4 on the primary
`T_bootstrap/r` endpoint is 0.977892.
```
## Stage 155: Same-Format Frontier Refresh

Goal:

```text
Use current full-SAB and body-profile evidence to close or route the remaining
same-format MAT-RLWE SAB optimization frontier after Stage154.
```

Status:

```text
Completed. Stage155 records PASS_STAGE155_SAME_FORMAT_FRONTIER_ROUTE_TO_REPRESENTATION_GATE. The measured profile preserves the
573440 CMUX/MAT_EP/from_DFT schedule count, closes blind r=6 layout tuning,
and routes next to representation-changing feasibility gates.
```
## Stage 156: Lazy-DFT Closure Gate

Goal:

```text
Test whether the Stage155 materialization frontier can be attacked by a naive
DFT-only accumulator state across SAB CMUX/RGSW updates.
```

Status:

```text
Completed. Stage156 records REJECT_STAGE156_NAIVE_LAZY_DFT_STATE_NOT_CLOSED. The production API requires torus
input for MAT EP, and finite MOSFHET-style decomposition tests show
nonlinearity under addition, negation, and negacyclic sign rotations.
```
## Stage 157: Sub-Decompose Fusion Preflight

Goal:

```text
Test whether direct decompose(in2-in1) is a viable same-format implementation
candidate after naive lazy DFT is rejected.
```

Status:

```text
Completed. Stage157 records PASS_STAGE157_SUB_DECOMP_FUSION_PREFLIGHT_POSITIVE_IMPLEMENTATION_CANDIDATE. It is an isolated C microbench only;
any positive result still requires a guarded production path and full-SAB
T_bootstrap/r gate.
```
## Stage 158: Sub-Decompose Fusion Full-SAB Gate

Goal:

```text
Integrate Stage157 sub-decompose fusion behind an explicit flag and test
complete SAB T_bootstrap/r against the same H14 r=6 backend control.
```

Status:

```text
Completed. Stage158 records SMOKE_STAGE158_SUB_DECOMP_FUSION_FULLSAB_POSITIVE_REPEATED_REQUIRED. Defaults remain unchanged.
```
## Stage 159: Sub-Decompose Fusion Repeated Gate

Goal:

```text
Upgrade Stage158 sub-decompose fusion from one-run full-SAB smoke to repeated
T_bootstrap/r, final-output noise, and resource gates.
```

Status:

```text
Completed. Stage159 records PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE. Scalar/default paths remain unchanged.
```
## Stage 160: Post-Fusion Frontier

Goal:

```text
Refresh the profile frontier after Stage159 sub-decompose fusion and choose the
next non-theoretical optimization target from actual component shares.
```

Status:

```text
Completed. Stage160 records PASS_STAGE160_POST_FUSION_FRONTIER_RECORDED; next frontier is mat_ep_plus_subdecomp;0.623301.
```
## Stage 161: Post-Fusion Attribution

Goal:

```text
Attribute the Stage160 dominant fused MAT EP/decompose block with native
counters if available, otherwise with explicitly scoped proxy evidence.
```

Status:

```text
Completed. Stage161 records PASS_STAGE161_PROXY_ATTRIBUTION_NATIVE_COUNTER_REQUIRED; WSL perf is not treated as native
counter evidence when unavailable.
```
## Stage 162: Materialization-Count Feasibility

Goal:

```text
Decide whether the current exact same-format PVW/MAT-SAB path can reduce the
573440 from_DFT materializations without a representation/API change.
```

Status:

```text
Completed. Stage162 records PASS_STAGE162_COUNT_REDUCTION_SAME_FORMAT_CLOSED_REP_CHANGE_REQUIRED; same-format count reduction is closed,
while backend batching and representation-changing exact states remain separate
routes.
```
## Stage 163: From-DFT Backend Batching Microbench

Goal:

```text
Measure whether backend batching or component-major loop order can lower each
from_DFT materialization's wall time after Stage162 closes same-format count
reduction.
```

Status:

```text
Completed. Stage163 records NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED. This is backend wall-time evidence
only; it does not reduce the 573440 materialization count and cannot be used
as a complete-SAB acceleration claim without a later T_bootstrap/r gate.
```
## Stage 164: Representation Closure Route

Goal:

```text
Combine the compact-closure, lazy-DFT, materialization-count, and backend
batching evidence to select the next non-speculative representation route.
```

Status:

```text
Completed. Stage164 records PASS_STAGE164_REPRESENTATION_ROUTE_TO_CLOSED_FULL_MAT_STREAMING_GATE. It routes next to a closed full-MAT
decompose/DFT streaming microbench and keeps structured compact keygen work
behind algebra/security/noise proof gates.
```
## Stage 165: Closed Full-MAT Streaming Microbench

Goal:

```text
Test whether row-streaming decompose/DFT/addmul beats the current all-row r=6
tiled AVX512 closed full-MAT external product.
```

Status:

```text
Completed. Stage165 records REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX. The route is microbench-only and does
not modify production SAB code.
```
## Stage 166: Shared-Output Compact Algebra Gate

Goal:

```text
Test whether shared-output compact SAB is a generic exact implementation route
or requires a new structured keygen/noise proof.
```

Status:

```text
Completed. Stage166 records PASS_STAGE166_GENERIC_COMPACT_EXACTNESS_BLOCKED_KEYGEN_PROOF_REQUIRED. Generic compact exactness is blocked
by missing body-to-body cross terms; compact SAB remains proof-driven, not an
implementation-ready optimization.
```
## Stage 167: CB5 Native r=6 Counter Refresh

Goal:

```text
Refresh native Linux perf-counter attribution for the current exact r=6
post-fusion PVW/MAT-SAB path.
```

Status:

```text
Completed. Stage167 records PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED. Counter evidence is attribution-only
and remains separate from theoretical optimality claims.
```
## Stage 168: Native Counter Frontier

Goal:

```text
Convert Stage167 native counters into scoped attribution, claim policy, and
next executable gates.
```

Status:

```text
Completed. Stage168 records PASS_STAGE168_ROUTE_TO_NATIVE_REPEATED_AND_SPLIT_COUNTERS. Native counters are attribution-only;
the next gates are native no-perf repeated full-SAB A/B and split native
component counters.
```
## Stage 169: CB5 Native Repeated r=6 Gate

Goal:

```text
Run native no-perf repeated complete-SAB A/B for the current exact r=6
PVW/MAT-SAB path using T_bootstrap/r as the primary endpoint.
```

Status:

```text
Completed. Stage169 records PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE. This is native repeated throughput
evidence for the current exact path, separate from component attribution and
theoretical optimality.
```
## Stage 170: Native Split Counter Microbench

Goal:

```text
Isolate native perf counters for the current exact r=6 MAT EP/subdecomp
boundary and the current from_DFT materialization boundary.
```

Status:

```text
Completed. Stage170 records PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED. The evidence is component-level
native counter attribution and remains separate from complete-SAB throughput
and theoretical optimality.
```
## Stage 171: Structured Compact Keygen Feasibility

Goal:

```text
Decide whether shared-output/compact MAT-SAB is an implementation-ready route
or a bounded proof route requiring new keygen, phase, noise, and security work.
```

Status:

```text
Completed. Stage171 records PASS_STAGE171_STRUCTURED_COMPACT_PROOF_ROUTE_NOT_IMPLEMENTATION_READY. Structured compact is finite-field
feasible under zero-cross logical constraints but remains blocked for
production SAB until proof obligations close.
```
## Stage 172: Frontier Closeout

Goal:

```text
Close the Stage169-171 evidence loop, record allowed/blocked claims, and route
the next bounded experiment.
```

Status:

```text
Completed. Stage172 records PASS_STAGE172_FRONTIER_CLOSEOUT_RECORDED. The next automatic engineering route
is Stage174 from_DFT locality; Stage173 remains a separate proof route.
```
## Stage 174: From-DFT Direct-Scale Gate

Goal:

```text
Test a bounded from_DFT locality/SIMD candidate by replacing the direct
spqlios scale/copy loop with an explicit AVX512 path behind a flag.
```

Status:

```text
Completed. Stage174 records NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED.
Microbench evidence is a promotion filter; complete-SAB claims require the
full-SAB gate.
```
## Stage 175: Post-Stage174 Frontier Refresh

Goal:

```text
Close the neutral direct-scale backend branch and route the next bounded
research step.
```

Status:

```text
Completed. Stage175 records PASS_STAGE175_ROUTE_TO_STRUCTURED_COMPACT_TOY_GATE. Direct-scale is not promoted; the next
bounded route is Stage173 structured compact finite phase/noise toy.
```
## Stage 173: Structured Compact Phase/Noise Toy

Goal:

```text
Run finite-field phase propagation and noise toy gates for the structured
compact MAT-SAB route.
```

Status:

```text
Completed. Stage173 records PASS_STAGE173_PHASE_NOISE_TOY_PROOF_STILL_OPEN. The route passes finite/toy checks but
does not yet have implementation permission because security and API proof
obligations remain open.
```
## Stage 176: Structured Compact Security/API Gate

Goal:

```text
Decide whether the structured compact route has enough security/API closure to
enter SAB implementation.
```

Status:

```text
Completed. Stage176 records BLOCK_STAGE176_STRUCTURED_COMPACT_SECURITY_API_NOT_CLOSED_REDIRECT_FULL_MAT. Compact SAB implementation permission
is denied because standard key-distribution proof and shared-mask accumulator
closure are not both satisfied. Executable optimization returns to the exact
full-MAT PVW/MAT-SAB path.
```
## Stage 177: Verified Literature/Novelty Gate

Goal:

```text
Verify real related work and decide which novelty/performance claims are allowed
before continuing implementation or paper writing.
```

Status:

```text
Completed. Stage177 records PASS_STAGE177_VERIFIED_LITERATURE_BOUNDARY_NO_STRONG_NOVELTY_CLAIM. Strong novelty claims are denied;
the next executable route is Stage178 exact full-MAT `T_bootstrap/r`
frontier selection.
```
## Stage 178: Full-MAT Per-Bit Frontier

Goal:

```text
Re-normalize current complete-SAB evidence as T_bootstrap/r and select the next
exact full-MAT optimization candidate from measured component shares.
```

Status:

```text
Completed. Stage178 records PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT. Current exact r=6 speedup is
1.131666667x mean versus repeated
scalar on the complete-SAB T_bootstrap/r endpoint. Next route is an audit-only
MAT EP/subdecomp microarchitecture gate, not compact implementation.
```
## Stage 179: MAT EP Microarchitecture Audit

Goal:

```text
Audit whether current exact full-MAT r=6 still has an implementable AVX512
mechanism before writing more code.
```

Status:

```text
Completed. Stage179 records PASS_STAGE179_AUDIT_SELECT_MAT_EP_SPLIT_PROBE_NO_CODE. MAT-aware AVX512 exists; code
permission is denied until Stage180 splits sub_decompose, torus_to_DFT, and
tiled addmul timing inside the hot block.
```
## Stage 180: MAT EP Split Probe

Goal:

```text
Measure sub_decompose, torus_to_DFT, and tiled addmul inside the current exact
MAT EP/subdecomp block before opening any new code branch.
```

Status:

```text
Completed. Stage180 records PASS_STAGE180_SPLIT_PROBE_RECORDED. Split data supports only bounded candidate selection; Stage181 tested the sub-decompose candidate and Stage182 records the frontier.
```
## Stage 181: AVX512 Sub-Decompose Gate

Goal:

```text
Benchmark the default-off AVX512 sub-decompose implementation candidate and
decide whether it deserves a complete-SAB gate.
```

Status:

```text
Completed. Stage181 records REJECT_STAGE181_SUB_DECOMP_AVX512_NOT_FASTER. The default-off variant remains a negative ablation and must not be claimed as SAB acceleration.
```
## Stage 182: Exact Path Negative Frontier

Goal:

```text
Close the current exact full-MAT AVX512/subcomponent loop after Stage181 and
define which routes may proceed without blind retuning.
```

Status:

```text
Completed. Stage182 records PASS_STAGE182_EXACT_PATH_NEGATIVE_FRONTIER_RECORDED. The default-off AVX512
sub-decompose candidate is rejected; exact same-format blind tuning is closed.
Only a new addmul/DFT dataflow mechanism or the separately proof-gated compact
route may proceed.
```
## Stage 183: Addmul Dataflow Screen

Goal:

```text
Decide whether the remaining exact addmul component has a concrete untested
dataflow mechanism before writing code.
```

Status:

```text
Completed. Stage183 records PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION. The current project already has
MAT-aware AVX512 tiled/fulltile/bodymajor addmul variants, and prior gates
reject the obvious alternatives. No new exact addmul hot-path code is allowed
without a new assembly/counter-backed mechanism.
```
## Stage 184: Exact-Route Closeout Claim Refresh

Goal:

```text
Refresh the final exact-route claim ledger after Stage183 denies new exact
addmul code permission.
```

Status:

```text
Completed. Stage184 records PASS_STAGE184_EXACT_ROUTE_CLOSEOUT_CLAIM_REFRESH. The only allowed current exact-route
claim is scoped complete-SAB `T_bootstrap/r` speedup under recorded conditions.
AVX512 theoretical optimality, sub-decompose improvement, and implemented
compact MAT-SAB claims are denied.
```
## Stage 185: Research/Repro Package Refresh

Goal:

```text
Package the current MAT-RLWE/r-body SAB research loop into a claim-safe
reproducibility bundle while preserving open gaps.
```

Status:

```text
Completed. Stage185 records PASS_STAGE185_RESEARCH_REPRO_PACKAGE_REFRESH. The package maps the original
objective to current evidence, keeps `T_bootstrap/r` as the primary endpoint,
and explicitly leaves the overall goal active because optimality and compact
MAT-SAB implementation remain unproven.
```
## Stage 186: Compact Proof Unlock Audit

Goal:

```text
Audit whether compact/shared-output MAT-SAB has enough proof, security, API,
noise, performance, and literature evidence to enter production SAB code.
```

Status:

```text
Completed. Stage186 records BLOCK_STAGE186_COMPACT_PROOF_UNLOCK_NOT_READY. Stage138 provides a kernel-level
signal, but Stage139/176/177 still block implementation and strong claims.
Compact/shared-output MAT-SAB remains a proof route only.
```
## Stage 187: Compact Proof Obligation Draft

Goal:

```text
Convert compact/shared-output MAT-SAB blockers into theorem obligations,
falsification gates, and implementation entry rules.
```

Status:

```text
Completed. Stage187 records PASS_STAGE187_COMPACT_PROOF_DRAFT_IMPLEMENTATION_STILL_DENIED. It allows isolated proof probes but
keeps production compact SAB code denied until key distribution, closed-state,
phase, and noise obligations pass.
```
## Stage 188: Scoped Manuscript Skeleton

Goal:

```text
Create a manuscript skeleton from the scoped exact PVW/MAT-SAB evidence while
preserving forbidden-claim guardrails.
```

Status:

```text
Completed. Stage188 records PASS_STAGE188_SCOPED_MANUSCRIPT_SKELETON_READY. The skeleton reports the implemented
exact-route `T_bootstrap/r` evidence and treats compact/shared-output MAT-SAB
as proof-gated future work.
```
## Stage 189: Closed-State Linear Probe

Goal:

```text
Run an executable T2 proof probe for whether lane-local compact output masks
can be publicly collapsed into one shared PVW_TMLWE mask.
```

Status:

```text
Completed. Stage189 records PASS_STAGE189_T2_PUBLIC_CLOSURE_PROBE_DIRECT_SHARED_MASK_REJECTED. The direct public shared-mask
projection route is rejected for r>1; production compact SAB code remains
denied. Remaining routes require multimask state, secret correction/key
switching, dense re-expansion, or a new structured selector distribution proof.
```
## Stage 190: Selector Distribution Distinguisher

Goal:

```text
Run an executable T1 public-distribution probe for compact selector shortcuts.
```

Status:

```text
Completed. Stage190 records PASS_STAGE190_T1_SELECTOR_DISTRIBUTION_DISTINGUISHERS_RECORDED_IMPLEMENTATION_STILL_DENIED. Row deletion, deterministic zero rows,
and forced equal/shared masks are publicly distinguishable from the current
dense MAT_TRGSW distribution. Compact/shared-output SAB implementation remains
denied unless a new structured-key proof route is supplied.
```
## Stage 191: Secret-Correction Noise/Resource Gate

Goal:

```text
Evaluate the remaining T4 route: secret correction/key-switch closure after
lane-local compact output.
```

Status:

```text
Completed. Stage191 records PASS_STAGE191_T4_SECRET_CORRECTION_LOWER_BOUND_RECORDED_IMPLEMENTATION_DENIED. The route remains proof-only:
correction must fit a tight saved-time budget, preserve key/materialization
gains, and prove a repeated SAB noise recurrence. Production compact SAB code
remains denied.
```
## Stage 192: Compact Admission and Route Selection

Goal:

```text
Audit compact/shared-output implementation permission after Stage189-191 and
select the next bounded non-theory experiment route.
```

Status:

```text
Completed. Stage192 records PASS_STAGE192_COMPACT_IMPLEMENTATION_DENIED_ROUTE_EXACT_ADDMUL_PREFLIGHT. Compact/shared-output SAB production
code remains denied. The next executable route is Stage193 exact full-MAT
addmul dataflow preflight.
```
## Stage 193: Exact Addmul Dataflow Preflight

Goal:

```text
Screen exact full-MAT addmul dataflow candidates before implementation.
```

Status:

```text
Completed. Stage193 records PASS_STAGE193_EXACT_ADDMUL_PREFLIGHT_NO_CODE_ROUTE_DFT_MECHANISM. No addmul code candidate is promoted:
dec-register caching is below the complete-SAB projection gate, and prior
fulltile/bodymajor/streaming families remain rejected.
```
## Stage 194: Exact DFT/Conversion Preflight

Goal:

```text
Screen exact DFT/conversion mechanisms before implementation.
```

Status:

```text
Completed. Stage194 records PASS_STAGE194_EXACT_DFT_PREFLIGHT_NO_CODE_ROUTE_SCOPED_REFRESH. No local DFT/conversion code candidate
is promoted; route next to Stage195 scoped paper/repro refresh.
```
## Stage 195: Scoped Paper/Repro Refresh

Goal:

```text
Refresh the scoped paper/repro package after compact and exact local
implementation frontiers were audited.
```

Status:

```text
Completed. Stage195 records PASS_STAGE195_SCOPED_PAPER_REPRO_REFRESH_READY_GOAL_ACTIVE. The package is ready for scoped
reporting, while the broader research goal remains active.
```
## Stage 196: Public Source Refresh

Goal:

```text
Refresh public source and citation status after the scoped Stage195 paper/repro
package, without upgrading metadata into theorem-level claims.
```

Status:

```text
Completed. Stage196 records PASS_STAGE196_PUBLIC_SOURCE_REFRESH_METADATA_VISIBLE_FULLTEXT_REVIEW_BLOCKED. Public metadata/code routes are
visible, but reviewed full-text citation work for 2025/686 remains blocked in
the current environment.
```
## Stage 197: Metadata-Safe Citation Bank

Goal:

```text
Convert Stage195/196 claim boundaries into sentence-level writing support so
future manuscript work cannot silently upgrade metadata or local kernel evidence.
```

Status:

```text
Completed. Stage197 records PASS_STAGE197_METADATA_SAFE_CITATION_BANK_READY_GOAL_ACTIVE. Scoped writing now has a sentence
support bank, paragraph map, guard scan, and next-stage queue; the broader
research goal remains active.
```
## Stage 198: Metadata-Safe Manuscript Refresh

Goal:

```text
Generate a scoped manuscript refresh using only the Stage197 sentence support
bank and verify paragraph-level compliance.
```

Status:

```text
Completed. Stage198 records PASS_STAGE198_METADATA_SAFE_MANUSCRIPT_REFRESH_READY_GOAL_ACTIVE. The refreshed draft is metadata-safe
and compliance-checked, but not a final paper or a new implementation claim.
```
## Stage 199: Active Goal Requirement Verifier

Goal:

```text
Audit the active PVW/MAT-SAB research objective requirement-by-requirement and
select the next admissible route from actual evidence gaps.
```

Status:

```text
Completed. Stage199 records PASS_STAGE199_ACTIVE_GOAL_VERIFIER_RECORDED_GOAL_ACTIVE. The scoped evidence chain is usable,
but the full active goal remains open because formal, source-anchor, and
stronger completion evidence are incomplete.
```
## Stage 200: Formal Gap Model with Probe

Goal:

```text
Improve the active-goal formal lower-bound/gap requirement using explicit
assumptions plus executable finite counterexample probes.
```

Status:

```text
Completed. Stage200 records PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE. The exact same-format full-MAT route
now has a scoped gap model and finite shortcut rejections, while stronger
claims remain behind proof/source/implementation gates.
```
## Stage 201: Structured Selector Distribution Probe

Goal:

```text
Run finite public-distribution probes for structured selector candidates after
Stage200 identifies selector structure as an open proof obligation.
```

Status:

```text
Completed. Stage201 records PASS_STAGE201_STRUCTURED_SELECTOR_DISTRIBUTION_PROBE_PROOF_ONLY. Only random dummy padding survives
simple public-pattern checks, and it remains proof-only with no production code
permission.
```
## Stage 202: Dummy Padding Semantic Probe

Goal:

```text
Test the only Stage201 public-pattern-surviving selector route in a finite
semantic model, with explicit negative controls.
```

Status:

```text
Completed. Stage202 records PASS_STAGE202_DUMMY_PADDING_SEMANTIC_PROBE_PROOF_ONLY. Dummy padding is semantically viable
only in a toy zero-semantic model and remains proof-only; keygen, security,
resource, noise, and complete-SAB gates are still missing.
```
## Stage 203: Production Selector Equation Probe

Goal:

```text
Check a declared production-shaped selector equation candidate for the dummy
padding proof route using finite phase/noise probes and negative controls.
```

Status:

```text
Completed. Stage203 records PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY. The declared equation candidate passes
finite phase/negative-control checks, but remains proof-only because production
keygen, security/noise, and complete-SAB gates are missing.
```

## Stage 204: Source Anchor Intake

Goal:

```text
Ground the active 2025/686 work in real public sources without overstating
metadata-only evidence as theorem or implementation proof.
```

Status:

```text
Completed. Stage204 records PASS_STAGE204_SOURCE_ANCHOR_INTAKE_METADATA_ONLY.
Real source metadata and implementation-environment policy are recorded, while
full-text theorem/equation anchors and production keygen gates remain open.
```

## Stage 205: Current Platform Probe

Goal:

```text
Return from source/theory gates to executable current-head evidence: WSL
platform probe, current scalar/PVW smoke, and sequential complete-SAB A/B using
the amortized T_bootstrap/r endpoint.
```

Status:

```text
Completed. Stage205 records PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB.
WSL/spqlios_avx512 smoke passes and sequential r=2/r=4 complete-SAB A/B is
positive, but hardware-counter attribution is blocked because perf is missing
and the A/B evidence is small-sample only.
```

## Stage 206: Current-Head High-Stat Evidence

Goal:

```text
Upgrade Stage205 small-sample evidence to current-head high-stat engineering
evidence: r=2/r=4 complete-SAB A/B with 10 runs and final-output noise with
20 seeds, all measured under T_bootstrap/r.
```

Status:

```text
Completed. Stage206 records PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE.
r=2/r=4 high-stat complete-SAB A/B and 20-seed noise gates pass, while
hardware counters, full-text theorem anchors, resource refresh, and broader
parameter/branch claims remain separate gates.
```
## Stage 207: Current-Head Resource Refresh

Goal:

```text
Refresh key size, keygen, and RSS costs for the current-head explicit
PVW/MAT-SAB path after Stage206 high-stat complete-SAB evidence.
```

Status:

```text
Completed. Stage207 records PASS_STAGE207_CURRENT_HEAD_RESOURCE_REFRESH. For the same current-head path used
by Stage206, r=2 has throughput speedup 1.299817x,
key bytes ratio 1.013617x, keygen-per-lane ratio
1.101017x, and max-RSS ratio 0.989539x.
r=4 has throughput speedup 1.356445x,
key bytes ratio 1.065349x, keygen-per-lane ratio
1.197131x, and max-RSS ratio 0.997004x.
The result is a current-head resource/cost refresh, not a statistical resource
distribution or optimality proof.
```
## Stage 208: Current-Head Profile Attribution

Goal:

```text
Refresh profile-only attribution for the current-head explicit active-buffer
PVW/MAT-SAB path after Stage206 throughput and Stage207 resource gates.
```

Status:

```text
Completed. Stage208 records PASS_STAGE208_CURRENT_HEAD_PROFILE_ATTRIBUTION. Active-buffer schedule counts pass
for r=2/r=4 with CMUX/MAT EP 573440, NCMUX 5080, and copyback 0. MAT EP is
the largest CMUX subcomponent: 40.879% of CMUX time for
r=2 and 47.760% for r=4. Post-processing remains below
the 2% implementation threshold, with max tail 1.218%
for r=2 and 1.222% for r=4.
```
## Stage 209: Current-Head MAT-EP Split Preflight

Goal:

```text
Split current-head r=2/r=4 MAT external-product cost into sub_decompose,
torus_to_DFT, and addmul_from_dec_dft before authorizing any new hot-path code.
```

Status:

```text
Completed. Stage209 records PASS_STAGE209_CURRENT_HEAD_MAT_EP_SPLIT_PREFLIGHT. Correctness passes for all r=2/r=4
split variants. The top route by estimated full-SAB share is torus_to_dft_rows
at r=4 with estimated full-SAB share 0.238961.
This is preflight evidence only; implementation and complete-SAB speedup claims
remain gated by Stage210+.
```
## Stage 210: Candidate Admission

Goal:

```text
Turn Stage209 split measurements into explicit code-admission policy.
```

Status:

```text
Completed. Stage210 records PASS_STAGE210_SELECT_DFT_ROWS_PREFLIGHT_NO_HOTPATH_CODE. Existing DFT batching/direct-scale,
direct sub-decompose, and addmul retile routes are denied for hot-path code.
Only a genuinely new FFT/dataflow preflight is admitted as Stage211.
```
## Stage 211: FFT/DFT Dataflow Preflight

Goal:

```text
Audit whether the admitted DFT/FFT dataflow route has a current source-level
mechanism concrete enough for production SAB hot-path implementation.
```

Status:

```text
Completed. Stage211 records PASS_STAGE211_DFT_DATAFLOW_PREFLIGHT_DENY_HOTPATH_CODE. The current code exposes single-row
torus-to-DFT APIs and row-loop MAT-EP conversions; old same-format DFT routes
remain denied by prior gates. The only admitted continuation is a standalone
multirow FFT/backend API probe or native counter refresh, not production SAB
hot-path edits at this stage.
```
## Stage 212: Multirow FFT API Probe

Goal:

```text
Execute a standalone multirow reverse-DFT wrapper probe for the current
SPQLIOS primitive before considering SAB hot-path integration.
```

Status:

```text
Completed. Stage212 records PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213. The probe is correctness-gated for
3-row and 5-row MAT cases and uses T_bootstrap/r research discipline by
requiring a component win before any complete-SAB claim. See
repro/stage212_multirow_fft_api_probe/comparison.csv for the promotion result.
```
## Stage 213: DFT Wrapper Integration Preflight

Goal:

```text
Integrate the Stage212 multirow reverse-DFT wrapper behind an explicit flag
and decide whether complete-SAB A/B is authorized.
```

Status:

```text
Completed. Stage213 records PASS_STAGE213_DFT_WRAPPER_COMPONENT_ONLY. The scalar/default path remains
unchanged because `MAT_TRGSW_MULTIROW_DFT_WRAPPER` is default-off.
```
## Stage 214: Frontier Native Counter Handoff

Goal:

```text
Close the post-Stage213 local route ledger and prepare a credential-free native
hardware-counter handoff for the next evidence route.
```

Status:

```text
Completed. Stage214 records PASS_STAGE214_FRONTIER_NATIVE_COUNTER_HANDOFF_READY. Local WSL lacks `perf`, CB5 SSH port
is reachable, and non-interactive SSH auth is not configured in this session.
No new hot-path code is authorized without Stage215 native counters or a new
formal compact proof.
```
## Stage 215: Native Counter Execution

Goal:

```text
Execute the Stage214 native counter handoff and decide whether native split
counters reopen any implementation route.
```

Status:

```text
Completed. Stage215 records PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN. Complete-SAB speedup remains a
separate gate and is not claimed from counter evidence alone.
```
## Stage 216: Post-Counter Frontier

Goal:

```text
Use Stage215 native counter evidence to decide whether any exact hot-path code
is authorized, and if not, select the next bounded non-theory research gate.
```

Status:

```text
Completed. Stage216 records PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT. Exact wrapper retuning and immediate
complete-SAB A/B for the wrapper are denied; the next selected executable route
is compact selector keygen/security/noise preflight outside the SAB hot path.
```
## Stage 217: Compact Keygen/Security Preflight

Goal:

```text
Run executable public-pattern, equation/resource, and admission gates for the
compact selector keygen route selected by Stage216.
```

Status:

```text
Completed. Stage217 records PASS_STAGE217_PATTERN_ONLY_KEYGEN_PREFLIGHT_NO_SAB_CODE. Count-matched random dummy padding
survives only a simple public-pattern screen; SAB hot-path code remains denied.
The next selected route is an isolated compact key-object/noise prototype.
```
## Stage 218: Compact Key-Object/Noise Prototype

Goal:

```text
Run an isolated finite key-object/noise prototype for the compact selector route
without touching SAB hot paths.
```

Status:

```text
Completed. Stage218 records PASS_STAGE218_COMPACT_KEY_OBJECT_PROTOTYPE_READY_API_SKELETON. The finite prototype passes phase,
negative-control, and toy-noise gates; the next route is a MOSFHET-adjacent
API skeleton only, not SAB integration.
```
## Stage 219: MOSFHET Compact Key API Skeleton

Goal:

```text
Compile-check a MOSFHET-adjacent compact key API skeleton after Stage218,
without touching SAB hot paths.
```

Status:

```text
Completed. Stage219 records PASS_STAGE219_MOSFHET_COMPACT_KEY_API_SKELETON_READY_ENCRYPTED_KEYGEN. The compact key row-role API skeleton
passes build/compile/run gates and routes next to encrypted compact keygen
prototype only; SAB integration remains denied.
```
## Stage 220: Encrypted Compact Keygen Prototype

Goal:

```text
Prototype encrypted compact keygen rows with semantic-zero dummy role
preservation and negative controls, without touching SAB hot paths.
```

Status:

```text
Completed. Stage220 records PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE. Encrypted compact keygen rows pass
phase/DFT/public-pattern/negative/noise gates and route next to production
noise recurrence; SAB integration remains denied.
```
## Stage 221: Compact Keygen Noise Recurrence

Goal:

```text
Bind encrypted compact keygen rows to a SAB schedule-level relative
noise/resource recurrence and decide whether isolated compact EP experiments
are allowed.
```

Status:

```text
Completed. Stage221 records PASS_STAGE221_COMPACT_KEYGEN_NOISE_RECURRENCE_READY_ISOLATED_EP. Relative dense-vs-active recurrence and
`T_bootstrap/r` row normalization pass, but only isolated compact EP experiments
are authorized; SAB hot-path integration remains denied.
```
## Stage 222: Isolated Compact EP Integration

Goal:

```text
Compile and run current MOSFHET compact EP as an isolated production-code probe,
then decide whether it covers the complete Stage203/SAB selector.
```

Status:

```text
Completed. Stage222 records FAIL_STAGE222. The production compact EP lane-local
subclass is correct, but complete selector/SAB integration remains denied
because neighbor/cross-body active equations are outside the current state
shape.
```
## Stage 223: Route Selection After Compact EP Denial

Goal:

```text
Select the next executable route after Stage222 proves lane-local compact EP is
not enough for complete SAB selector integration.
```

Status:

```text
Completed. Stage223 records PASS_STAGE223_ROUTE_EXACT_PVW_MAT_REFRESH_SELECTED_COMPACT_COMPLETE_DENIED. The exact closed dense MAT/PVW path is
selected for Stage224 AVX/resource refresh under T_bootstrap/r; compact
complete-SAB integration remains denied.
```
## Stage 224: Exact PVW/MAT AVX Resource Refresh

Goal:

```text
Rerun complete-SAB T_bootstrap/r performance for the exact closed dense MAT/PVW
mainline selected after compact complete-SAB denial.
```

Status:

```text
Completed. Stage224 records PASS_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_POSITIVE. It refreshes exact PVW/MAT full-SAB
performance and preserves the compact complete-SAB denial boundary.
```
## Stage 225: Exact Refresh Noise/Resource Rerun

Goal:

```text
Rerun fresh correctness/noise and resource side conditions for the exact
PVW/MAT backend path refreshed in Stage224.
```

Status:

```text
Completed. Stage225 records PASS_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE. It strengthens the exact-route evidence
package without changing scalar/default behavior or the compact complete-SAB
denial.
```
## Stage 226: Exact MAT/PVW Counter Attribution

Goal:

```text
Attribute the Stage224 exact-route backend-vs-wrapper delta using native
cycles/load/store/FMA counters where available.
```

Status:

```text
Completed at `8e28f16` with `PASS_STAGE226_COUNTERS_RECORDED_TIMING_NEUTRAL`. The result is an attribution gate:
it does not claim theoretical optimality or reopen the compact SAB route.
```
## Stage 227: Exact Route Claim Boundary Update

Goal:

```text
Freeze the supported and blocked claims after Stage224/225/226 so the next
work stays implementation- and evidence-driven.
```

Status:

```text
Completed at `df8db1f` with `PASS_STAGE227_EXACT_ROUTE_CLAIM_BOUNDARY_FIXED`. The primary metric is complete-SAB
`T_bootstrap/r`; theoretical optimality and compact-route claims remain blocked.
```
## Stage 228: Counter-Driven Backend Kernel Search

Goal:

```text
Use Stage226 native counters and prior frontier gates to decide whether any
new exact MAT/PVW hot-path code is justified.
```

Status:

```text
Completed at `f2b753f` with `PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX`. No speculative hot-path edit is
permitted; next selected work is parameter generalization.
```
## Stage 229: Parameter Generalization Matrix

Goal:

```text
Freeze the complete-SAB `T_bootstrap/r` parameter evidence matrix before
broadening exact PVW/MAT-SAB claims.
```

Status:

```text
Generated from input head `cf19098` with `PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED`. Binary target and added-parameter
evidence is recorded, non-binary PVW-SAB remains unsupported, and all-parameter
or theoretical-optimality claims remain blocked.
```
## Stage 230: Source-Verified Literature Novelty Audit

Goal:

```text
Refresh the related-work and novelty boundary for PVW/MAT-SAB using real
primary or official metadata sources.
```

Status:

```text
Generated from input head `4a6eda3` with `PASS_STAGE230_SOURCE_VERIFIED_SCOPED_NOVELTY_BOUNDARY`. The allowed contribution
remains scoped systems/engineering evidence under complete-SAB `T_bootstrap/r`;
broad shared-mask, batch, PVW-packing, non-binary, and theoretical-optimality
claims remain blocked.
```
## Stage 231: Current-Head Added-Parameter Refresh

Goal:

```text
Refresh added binary parameter evidence at current head without promoting
single-run smoke into a paper-level statistical claim.
```

Status:

```text
Generated from input head `a2b7c43` with `PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING`. `SET_4_5_2048` and
`SET_2_3_4096` pass current-head shape, complete-SAB A/B smoke, and one-seed
noise smoke for r=2/r=4. Full statistics and resource refresh remain pending.
```
## Stage 232: Selected Current-Head Full-Stat/Resource Preflight

Goal:

```text
Run a representative current-head added-parameter preflight with complete-SAB
`T_bootstrap/r`, noise, and resource side conditions without promoting it to a
full parameter-matrix claim.
```

Status:

```text
Generated from input head `db72720` with `PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING`. `SET_2_3_4096`, r=4
passes selected-subset 3-run complete-SAB A/B, 3-seed noise, and resource
recording. Full added-parameter matrix statistics remain pending.
```
## Stage 233: First High-Stat Added-Parameter Slice

Goal:

```text
Promote one added-parameter current-head slice from smoke/preflight to
10-run/20-seed/resource evidence under complete-SAB `T_bootstrap/r`.
```

Status:

```text
Generated from input head `b1064ed` with `PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING`. `SET_4_5_2048`, r=4
passes 10-run complete-SAB A/B, 20-seed noise, and resource recording. The full
added-parameter matrix remains pending.
```
## Stage 234: Second High-Stat Added-Parameter Slice

Goal:

```text
Promote SET_4_5_2048 r=2 from smoke/preflight to 10-run/20-seed/resource
evidence under complete-SAB `T_bootstrap/r`.
```

Status:

```text
Generated from input head `4e7facc` with `PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING`. `SET_4_5_2048`, r=2
passes 10-run complete-SAB A/B, 20-seed noise, and resource recording. Together
with Stage233, SET_4_5_2048 r=2/r=4 is covered; SET_2_3_4096 remains pending.
```
## Stage 235: SET_2_3_4096 r=2 High-Stat Slice

Goal:

```text
Promote SET_2_3_4096 r=2 from smoke/preflight evidence to 10-run/20-seed/resource
evidence under complete-SAB T_bootstrap/r.
```

Status:

```text
Generated from input head `c8dae05` with `PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING`. `SET_2_3_4096`, r=2
passes 10-run complete-SAB A/B, 20-seed noise, and resource recording. The
added-parameter matrix still requires SET_2_3_4096 r=4 high-stat evidence.
```
## Stage 236: SET_2_3_4096 r=4 High-Stat Slice

Goal:

```text
Promote SET_2_3_4096 r=4 from preflight to 10-run/20-seed/resource evidence
under complete-SAB T_bootstrap/r and close the selected binary added-parameter
matrix.
```

Status:

```text
Generated from input head `5475e49` with `PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE`. `SET_2_3_4096`, r=4
passes 10-run complete-SAB A/B, 20-seed noise, and resource recording. The
selected binary matrix for SET_4_5_2048 and SET_2_3_4096 at r=2/r=4 is now
high-stat complete, with broader claims still gated.
```
## Stage 237: Scoped Manuscript Package

Goal:

```text
Convert the selected binary PVW/MAT-SAB matrix into a scoped manuscript/report
package with section evidence, claim ledger, source policy, candidate-path
matrix, overclaim guard, and next-stage gates.
```

Status:

```text
Generated from input head `d825eec` with `PASS_STAGE237_SCOPED_MANUSCRIPT_PACKAGE_READY_CLAIM_BOUNDED`. The package is ready for
source-verified citation finalization or optional native-counter attribution.
It remains bounded to exact dense binary PVW/MAT-SAB under complete-SAB
T_bootstrap/r.
```
## Stage 238: Source-Verified Citation Package

Goal:

```text
Bind Stage237 draft claims to source-verified rows or local repro evidence,
record current URL access, and prevent BibTeX/citation hallucination.
```

Status:

```text
Generated from input head `eff2c0d` with `PASS_STAGE238_SOURCE_VERIFIED_CITATION_PACKAGE_READY_NO_BIBTEX_HALLUCINATION`. Citation support is ready
for a scoped draft. BibTeX remains TODO until retrieved from verified sources.
```
## Stage 239: Verified BibTeX Retrieval and LaTeX Stub

Goal:

```text
Retrieve BibTeX from verified routes where possible, keep unresolved sources as
TODOs, and create a minimal LaTeX stub without generating references from
memory.
```

Status:

```text
Generated from input head `2b4fa33` with `PASS_STAGE239_PARTIAL_VERIFIED_BIBTEX_LATEX_STUB_READY_TODOS_REMAIN`. Retrieved 9
verified BibTeX entries and recorded 2 unresolved TODOs.
```
## Stage 240: Scoped LaTeX Draft

Goal:

```text
Convert verified Stage239 citations and Stage236 selected binary complete-SAB
evidence into a scoped LaTeX draft with claim/citation gates.
```

Status:

```text
Generated from input head `2e3f230` with `PASS_STAGE240_SCOPED_LATEX_DRAFT_READY_CLAIMS_AUDITED`. The draft is ready for a
compile/template pass, while unresolved BibTeX rows, current-head counter
refresh, non-binary support, compact route, and theoretical optimality remain
separate gates.
```
## Stage 241: LaTeX Compile Package

Goal:

```text
Compile the Stage240 scoped LaTeX draft with BibTeX and record PDF/log gates.
```

Status:

```text
Generated from input head `fe28338` with `PASS_STAGE241_LATEX_COMPILE_PACKAGE_READY`. The scoped draft now has
resolved compile evidence. Remaining gates are bibliography TODO closure,
optional current-head counter wording, and any broader algorithmic route.
```
## Stage 242: Unresolved BibTeX Follow-Up

Goal:

```text
Resolve remaining BibTeX TODOs where verified routes exist, without generating
references from memory.
```

Status:

```text
Generated from input head `359232c` with `PASS_STAGE242_BIBTEX_TODO_REDUCED_BATCHBOOT_REMAINS`. `LW23A_B` is split into
two verified DBLP BibTeX entries. `BATCHBOOT26` remains an explicit TODO until
an official BibTeX route exists.
```
## Stage 243: Apply LW Citations and Recompile

Goal:

```text
Patch the scoped draft with verified LW23A/LW23B citations and rerun compile
gates while keeping BatchBoot as TODO.
```

Status:

```text
Generated from input head `e049e91` with `PASS_STAGE243_LW_CITATIONS_APPLIED_RECOMPILED_BATCHBOOT_TODO`. The scoped draft now
compiles with 11 resolved citation keys, including Batch Bootstrapping I/II.
`BATCHBOOT26` remains a visible TODO until official BibTeX is available.
```
## Stage 244: BatchBoot BibTeX Monitor

Goal:

```text
Reprobe official BatchBoot citation routes and preserve no-hallucination
bibliography policy.
```

Status:

```text
Generated from input head `b5c7cda` with `PASS_STAGE244_BATCHBOOT_MONITOR_RECORDED_NO_VERIFIED_BIBTEX`. No verified BatchBoot
BibTeX export was found through USENIX, DBLP, or Crossref probes. BatchBoot
remains an explicit TODO.
```
## Stage 245: Current-Head Counter Bridge

Goal:

```text
Audit whether Stage226 native counter attribution remains valid for the current
head by checking executable MAT/PVW-SAB hot-path deltas.
```

Status:

```text
Generated from input head `0888285` with `PASS_STAGE245_COUNTER_REUSE_BRIDGED_NO_HOTPATH_DELTA`. The Stage226 native
counter evidence is bridged as attribution-only because no tracked hot-path
source delta exists after Stage226. It is not a new timing or optimality claim.
```
## Stage 246: Broader Algorithm Admission Gate

Goal:

```text
Classify non-binary, compact, exact-dense, and optimality routes before any
broader production SAB implementation.
```

Status:

```text
Generated from input head `e2b3595` with `PASS_STAGE246_BROADER_ALGORITHM_GATE_RECORDED_PROOF_PROTOTYPES_ONLY`. No broader production
claim is promoted. Generic compact is rejected under existing counterexamples;
structured compact is admitted only to a finite/proof prototype; non-binary
PVW remains blocked until selector semantics are defined.
```
## Stage 248: Structured Compact Finite Probe

Goal:

```text
Run the Stage246 structured compact proof prototype in a finite r=2 model.
```

Status:

```text
Generated from input head `74aaee0` with `PASS_STAGE248_STRUCTURED_COMPACT_FINITE_ALGEBRA_PASS_SECURITY_BLOCKED`. The off-lane-zero
structured compact algebra and toy noise probes pass, but selector
distribution, keygen security, ring-level noise, and complete-SAB value remain
blocked. No production compact SAB implementation is admitted.
```
## Stage 249: Structured Compact Distribution/Security Preflight

Goal:

```text
Decide whether Stage248's structured compact proof prototype can enter
production SAB implementation.
```

Status:

```text
Generated from input head `1b904a7` with `PASS_STAGE249_COMPACT_SECURITY_PREFLIGHT_FREEZE_PRODUCTION_ROUTE`. Compact-saving public
distributions are distinguishable, and the only public-pattern survivor uses
dummy random padding with dense public size and proof-only semantics. Compact
production integration is frozen until a formal distribution/keygen/security
proof exists.
```
## Stage 250: Exact Dense Lower-Bound Gap

Goal:

```text
Refresh the exact dense PVW/MAT-SAB lower-bound/optimality boundary after the
compact production route is frozen.
```

Status:

```text
Generated from input head `b3dc1e0` with `PASS_STAGE250_EXACT_DENSE_GAP_REFRESH_OPTIMALITY_OPEN`. Complete-SAB
`T_bootstrap/r` evidence remains scoped and positive, but exact dense
optimality is still open. Compact/body-linear term models are not admissible
lower bounds, and no speculative hot-path code is permitted without a new
counter-backed mechanism.
```
## Stage 251: Non-Binary Selector Semantics

Goal:

```text
Audit scalar ternary/include-zero selector equations and decide whether current
PVW/MAT-SAB can implement non-binary branches.
```

Status:

```text
Generated from input head `727e736` with `PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION`. Scalar `s_sign/s_coff`
semantics are identified and finite rotation equations pass, but current
PVW/MAT-SAB has no MAT sign/coefficient selector families, rejects
`coeff != 1`, and guards the target harness to `BINARY`. Production
implementation is blocked; Stage252 must design a non-production selector/key
skeleton first.
```
## Stage 252: Non-Binary MAT Selector Key Skeleton

Goal:

```text
Define the non-production MAT selector key/storage/API skeleton needed for
include-zero and ternary PVW/MAT-SAB branches.
```

Status:

```text
Generated from input head `c5ed044` with `PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE`. Stage252 compiles and
runs an isolated selector-key skeleton with existing distance bits plus
optional `s_coff` and `s_sign` MAT selector families. Production SAB/PVW source
files remain unchanged; Stage253 isolated sub_a equivalence is the only
admitted next step.
```
## Stage 253: Isolated Non-Binary Sub_A Equivalence

Goal:

```text
Validate include-zero and ternary sub_a equations per PVW body lane using the
Stage252 selector-key skeleton.
```

Status:

```text
Generated from input head `3dac5c7` with `PASS_STAGE253_ISOLATED_NONBINARY_SUBA_EQUIVALENCE_READY_KEYGEN_NOISE_PREFLIGHT`. The finite negacyclic
lane model passes for include-zero and ternary branches at r=1/2/4, while the
binary naive update fails the negative controls. Production SAB/PVW source
files remain unchanged. Next selected route: encrypted selector keygen/noise
preflight.
```
## Stage 254: Non-Binary Keygen/Noise Preflight

Goal:

```text
Record selector keygen, noise, resource, and count obligations before actual
non-binary PVW/MAT selector implementation.
```

Status:

```text
Generated from input head `26bc1c4` with `PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE`. Existing MAT monomial
encryption and DFT conversion primitives can support an isolated `s_coff`/
`s_sign` prototype. Single-family count pressure is recorded and does not
block isolated prototyping, but production full SAB remains blocked until
actual keygen, noise/resource, and integration gates pass.
```
## Stage 255: MOSFHET Non-Binary Selector Keygen/Noise

Goal:

```text
Run actual MOSFHET-adjacent MAT s_coff/s_sign selector encryption and isolated
sub_a external-product phase/noise checks.
```

Status:

```text
Generated from input head `167c2ef` with `PASS_STAGE255_MOSFHET_SELECTOR_KEYGEN_NOISE_READY_NONBINARY_SPARSEMUL_PREFLIGHT`. Production MOSFHET MAT
0/1 selector encryption and external products pass isolated include-zero and
ternary sub_a phase gates for r=1/2/4. Production SAB/PVW source remains
unchanged; next selected route is non-binary sparse_mul integration preflight.
```
## Stage 256: Non-Binary Sparse_Mul Preflight

Goal:

```text
Design and gate non-binary sparse_mul integration before writing an explicit
implementation path.
```

Status:

```text
Generated from input head `0eecbc5` with `PASS_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT_READY_EXPLICIT_IMPLEMENTATION`. The integration boundary
is explicit: reuse binary distance-bit RGSW steps, add one MAT selector EP per
accumulator index per sparse step for either s_coff or s_sign, and preserve the
final RGSW step. Finite multi-round lifecycle probes pass for r=1/2/4. Stage257
may implement an explicit non-binary sparse_mul path only; full SAB speedup
remains blocked.
```

## Stage 257: Non-Binary Sparse_Mul Implementation

Goal:

```text
Add an explicit production-code PVW/MAT sparse_mul path for include-zero and
ternary selector families without replacing scalar SAB or binary PVW defaults.
```

Status:

```text
Generated from input head `c919276` with `PASS_STAGE257_NONBINARY_SPARSEMUL_IMPLEMENTED_STAGED`. The new
`sab_pvw_new_nonbinary_key`, `sab_pvw_sub_a_include_zero`,
`sab_pvw_sub_a_ternary`, and `sab_pvw_sparse_mul_nonbinary` APIs compile and
pass staged lane equivalence for include-zero and ternary at r=1/2/4. Full SAB
speedup and T_bootstrap/r claims remain blocked pending correctness/noise and
complete bootstrapping A/B.
```

## Stage 258: Non-Binary Sparse_Mul Correctness/Noise

Goal:

```text
Convert the Stage257 explicit non-binary PVW/MAT sparse_mul implementation into
a multi-trial correctness/noise gate before admitting full SAB integration.
```

Status:

```text
Generated from input head `1d69fa5` with `PASS_STAGE258_NONBINARY_SPARSEMUL_CORRECTNESS_NOISE`. include-zero and ternary
sparse_mul pass r=1/2/4, trials=3, with zero scalar/PVW pair failures across
all recorded body-lane coefficients. Stage259 full-SAB integration preflight is
admitted, but full bootstrapping acceleration and T_bootstrap/r remain blocked.
```

## Stage 259: Non-Binary Full SAB Smoke

Goal:

```text
Wire the explicit non-binary PVW/MAT sparse_mul route into complete SAB
bootstrapping without changing scalar SAB or binary PVW defaults.
```

Status:

```text
Generated from input head `16a18c1` with `PASS_STAGE259_NONBINARY_FULL_SAB_SMOKE`. The new explicit
non-binary full SAB API passes small FFNT full-pipeline equivalence for
include-zero and ternary r=1/2/4. Target-parameter noise, resource, and
T_bootstrap/r speedup remain blocked until Stage260+.
```

## Stage 260: Non-Binary Full SAB Noise/Resource

Goal:

```text
Upgrade the explicit non-binary PVW/MAT full SAB path from deterministic smoke
to a small multi-trial correctness/noise/resource gate.
```

Status:

```text
Generated from input head `cc6067f` with `PASS_STAGE260_NONBINARY_FULL_SAB_NOISE_RESOURCE`. include-zero and ternary
r=1/2/4 pass the small FFNT full-path final-noise gate with zero PVW, scalar,
and pair failures. Five stage-pair boundaries also record zero pair failures.
Stage261 target `T_bootstrap/r` benchmarking is admitted, but speedup remains
unproved.
```
## Stage 292: Direct DFT Full-SAB A/B

Goal: validate Stage291 direct sub-decompose-to-DFT under complete SAB
`T_bootstrap/r`.

Status: `PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED`.
## Stage 293: Direct DFT Target Correctness/Resource Smoke

Goal: validate Stage292 direct DFT target correctness and resource reporting.

Status: `PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING`. High-stat noise remains pending.
## Stage 294: Direct DFT Target Final-Output Noise

Goal: replace the old N=16 SPQLIOS noise fixture with a target-size
include-zero final-output noise gate for direct DFT.

Status: `PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT`.
## Stage 295: Direct DFT Stats Refresh

Goal: strengthen Stage292/294 evidence with repeated performance and noise
refresh.

Status: `PASS_STAGE295_DIRECT_DFT_STATS_REFRESH_HIGHSTAT_PENDING`.
## Stage 296: Direct DFT High-Stat Campaign

Goal: upgrade Stage295 evidence with a 10-run/10-trial same-backend complete
SAB campaign.

Status: `PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL`.
