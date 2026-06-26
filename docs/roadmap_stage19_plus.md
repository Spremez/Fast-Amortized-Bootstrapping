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
