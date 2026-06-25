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
