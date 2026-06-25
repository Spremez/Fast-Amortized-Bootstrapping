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
```
