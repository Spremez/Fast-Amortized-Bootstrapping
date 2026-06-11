# MAT External Product to Bootstrapping Optimization Audit

Date: 2026-06-11

Thread id under review:

```text
019ea56e-e5f5-7770-a3bd-cb2aec1c7da3
```

## Purpose

This audit consolidates the current analysis of MAT/shared-mask external
product performance and checks whether the project plan is sufficient to carry
the work from external-product optimization to full 2025/686 sparse amortized
bootstrapping (SAB) optimization.

## Goal Audit

Codex app-level goal status:

```text
active goal registered for the current thread
```

The active goal is to add and validate a `sab_pvw_*` optimization path without
breaking the existing scalar SAB path, then prove full SAB bootstrapping
throughput improvement through staged correctness, noise, performance, and
reproducibility gates.

Project-level goal status:

The repository does have a project roadmap in
`docs/roadmap_686_pvw_sab.md`. That roadmap is broad enough to cover the whole
optimization path:

```text
external product -> CMUX/NCMUX -> RGSW monomial -> sparse_mul ->
full sab_pvw_* bootstrapping -> noise/correctness -> performance ->
ablation -> report/paper package
```

Audit conclusion:

- The conceptual project goal is sufficient.
- The runtime/Codex goal is now registered.
- The roadmap needed a status refresh after the latest MAT experiments; this
  audit updates that status and identifies the next execution stage.

## Current Technical Conclusion

Current MAT external product is dense:

```text
rows = (k + r) * l
outputs = k + r
DFT addmul count = (k + r)^2 * l
```

For the current measured shape:

```text
N = 2048
k = 1
l = 1
Bgbit = 23
r in {1,2,4}
```

Operation counts:

| r | scalar rows | MAT rows | scalar DFT addmul | MAT DFT addmul |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 4 | 4 |
| 2 | 4 | 3 | 8 | 9 |
| 4 | 8 | 5 | 16 | 25 |

Therefore MAT does not win by reducing DFT multiplication count. It wins when
shared-mask savings in decomposition, DFT conversion, and inverse DFT dominate
the extra dense accumulation cost.

Strict same-backend algorithm evidence:

| implementation/backend | r=1 | r=2 | r=4 |
|---|---:|---:|---:|
| MOSFHET `spqlios` | 0.977x | 1.266x | 1.340x |
| MOSFHET `spqlios_avx512` | 0.928x | 1.199x | 1.216x |
| mbfhe `spqlios-fma` full-decomp | 1.038x | 1.236x | 1.292x |
| mbfhe `spqlios-fma` streaming | 1.008x | 1.228x | 1.326x |

Interpretation:

- `r=1`: no stable MAT advantage.
- `r=2`: MAT gives about `1.20x-1.27x` algorithmic speedup.
- `r=4`: MAT gives about `1.22x-1.34x` algorithmic speedup.
- The direction is consistent across MOSFHET and mbfhe when scalar and MAT are
  compared inside the same backend.

Same-level AVX/FMA MAT implementation comparison:

| r | MOSFHET MAT | mbfhe MAT full-decomp | MOSFHET / mbfhe |
|---:|---:|---:|---:|
| 1 | 18.726 | 17.659 | 1.060x |
| 2 | 29.112 | 27.754 | 1.049x |
| 4 | 54.352 | 55.542 | 0.979x |

Interpretation:

- After aligning both to 256-bit AVX/FMA level, the MAT implementation gap is
  small.
- mbfhe is slightly faster for `r=1,2`; MOSFHET is slightly faster for `r=4`
  in the recorded run.
- There is no strong evidence that either MAT implementation is decisively
  superior after SIMD level is aligned.

## Evidence Inventory

Implemented in this repository:

- `src/mosfhet/src/mattrgsw.c`
- `MAT_TRGSW_MUL_SCRATCH`
- `mat_trgsw_mul_pvmtmlwe_DFT(...)`
- `SAB_PVW_KERNEL_TEST=true`
- full-output scalar-vs-MAT benchmark in `main.c`
- AVX512 backend rules in `Makefile`
- MOSFHET `DFT_FMA_OPT` AVX/FMA path in `src/mosfhet/src/polynomial.c`

Evidence documents:

- `docs/roadmap_686_pvw_sab.md`
- `docs/stage3_pvw_kernel_status.md`
- `docs/mat_external_product_breakdown.md`

Key raw log directories:

- `build/bench_logs/mat_avx_mbfhe_20260611_133003`
- `build/bench_logs/mat_full_compare_20260611_133342`
- `build/bench_logs/strict_external_product_20260611_135128`
- `build/bench_logs/same_backend_fma_mat_compare_20260611_140333`

External mbfhe modification used for strict benchmarking:

- `D:\projects\mbfhe-mb\src\test\test-matrix-external-product-bench.cpp`
- added method: `scalar_repeat_full_ws`

## Stage Status

| Stage | Name | Status | Evidence | Next gate |
|---:|---|---|---|---|
| 0 | Baseline/platform | Done | WSL/Linux and Windows smoke records | Keep baseline reproducible |
| 1 | SAB protocol/cost map | Done enough | roadmap and prior cost map docs | Refresh if hot path changes |
| 2 | Bottleneck measurement | Done enough | profile docs and cost model | Re-profile after PVW integration |
| 3 | MAT external product kernel | Done for bring-up/perf analysis | stage3 doc and MAT breakdown doc | No direct SAB replacement yet |
| 4 | SAB-PVW state design | Not started | none | Write lane-state design and isolated CMUX tests |
| 5 | `sab_pvw_*` hot path | Not started | none | Integrate CMUX, then RGSW, then sparse_mul |
| 6 | Noise/correctness | Not started | none | Multi-seed per-lane correctness/noise |
| 7 | Performance evaluation | Partial only at external-product layer | MAT benches | Full SAB profile after Stage 5 |
| 8 | Ablation/variants | Not started | none | r-scaling, backend, layout, scratch ablations |
| 9 | Literature/novelty | Not started | none | related-work matrix before paper claim |
| 10 | final report/package | Not started | none | reproducibility pack and final tables |

Current execution point:

```text
Stage 3 is complete enough to enter Stage 4.
Do not claim final bootstrapping speedup yet.
```

## Optimization Directions

### Kernel-Level Optimizations

1. Remove explicit DFT-output clear:
   - initialize each output component from the first row using `mul`;
   - use `addmul` only for remaining rows;
   - expected benefit: removes current MAT clear overhead.

2. Fused row/output addmul:
   - current code calls one polynomial addmul per output component;
   - fused kernel should load one decomposed DFT row once and update all
     `k+r` output components in the same frequency loop;
   - this does not reduce arithmetic count, but should reduce loop overhead,
     repeated loads, and cache pressure.

3. Specialize small shapes:
   - `k=1,l=1,r=2`;
   - `k=1,l=1,r=4`;
   - unroll row and output loops for the expected SAB lane counts.

4. Streaming decomposition:
   - decompose one input component/level;
   - convert to DFT;
   - immediately accumulate;
   - compare against full materialization in MOSFHET, as mbfhe has a streaming
     variant.

5. AVX/FMA and AVX512 parity:
   - keep `DFT_FMA_OPT` for same-level mbfhe comparison;
   - keep `spqlios_avx512` for best MOSFHET performance;
   - if cross-library absolute speed matters, either add AVX512 to mbfhe or use
     a shared DFT addmul kernel.

6. Memory layout and alignment:
   - inspect `DFT_Polynomial` alignment;
   - avoid unaligned loads if safe;
   - test SoA-friendly row/output layout for fused kernels.

7. Prefetch and cache locality:
   - prefetch selector rows;
   - batch output component updates per row/frequency block;
   - measure memory bandwidth if `r` grows.

8. Sparse or diagonal structure:
   - only valid if selector representation is changed to contain structural
     zeros or diagonal relationships;
   - encrypted zeros cannot be skipped just because their message is zero;
   - requires correctness and noise proof.

### Algorithm-Level Optimizations

1. Choose the right batching boundary:
   - external product alone;
   - isolated CMUX/NCMUX;
   - RGSW monomial multiplication;
   - full `sparse_mul`.

2. Reuse shared schedule:
   - MAT is meaningful only when lanes share the same control/key schedule;
   - if lanes do not share schedule, MAT advantage weakens.

3. Strong scalar baseline:
   - consider a scalar-repeat baseline that caches shared mask decomposition or
     DFT conversions when mathematically valid;
   - this tests whether MAT still wins against a stronger scalar implementation.

4. r-scaling:
   - current reliable range is `r=1/2/4`;
   - larger `r` may lose because dense addmul grows as `(k+r)^2*l`;
   - test `r=8` only after fused or streaming kernels are ready.

5. Full-output boundary:
   - full-output MAT benefits from fewer inverse DFT conversions;
   - bootstrapping integration must track whether the next step consumes DFT or
     torus output.

### SAB Integration Optimizations

1. Stage 4 isolated CMUX/NCMUX:
   - completed for `r=1/2/4`;
   - encrypted-input CMUX selector `0/1` passes;
   - trivial-input raw-automorphism NCMUX selector `0/1` passes;
   - scalar `sab_rlwe_bootstrap(...)` remains unchanged and passes smoke.

2. Stage 5 RGSW monomial batching:
   - isolated scheduler tests now pass for `r=1/2/4`;
   - encrypted one-bit selector tests pass for selector bit `0/1`;
   - trivial-selector multibit tests pass for selector bits `{1,0,1}`;
   - full encrypted multibit tests pass for selector bits `{1,0,1}`;
   - PVW TMLWE automorphism/key-switch is implemented and verified against the
     scalar automorphism oracle.

3. Stage 5 `sparse_mul` batching:
   - isolated binary branch now passes for `r=1/2/4`, `h=2`, `r_prec=3`;
   - the check compares after each `RGSW_monomial_mul`, each binary `sub_a`,
     and the final `RGSW_monomial_mul`;
   - target-size `h=39, in_N=2048` and full bootstrapping output extraction are
     still not integrated.

4. Key and selector materialization:
   - define MAT selector generation from scalar selector schedule;
   - record memory/key-size impact;
   - avoid runtime materialization in hot loops.

5. Output/extract path:
   - implement per-lane extraction from PVW bodies;
   - keep packing keyswitch and HW-reducing keyswitch comparable.

6. Allocation and scratch management:
   - preallocate PVW/SAB scratch per bootstrap call or per context;
   - no allocation in CMUX/RGSW/sparse_mul hot loops.

### Correctness and Noise Optimizations

1. Deterministic equivalence tests:
   - scalar vs PVW after isolated CMUX;
   - scalar vs PVW after RGSW monomial;
   - scalar vs PVW after `sparse_mul`;
   - scalar vs PVW after full bootstrap.

2. Noise instrumentation:
   - record phase/noise at each stage;
   - compare per lane;
   - identify whether MAT accumulation changes noise growth.

3. Multi-seed protocol:
   - engineering signal: at least 50 seeds;
   - paper/report signal: higher seed count, confidence intervals, and failure
     model.

4. Parameter safety:
   - `pvmtmlwe_keyswitch(...)` is still a known aborting stub;
   - do not route through unimplemented PVW keyswitch paths.

### Measurement and Reproducibility

1. Report medians and confidence intervals:
   - current data has run-to-run noise;
   - final tables should include mean, median, stddev, min, p95.

2. Record exact backend:
   - `spqlios`;
   - `spqlios_avx512`;
   - `spqlios + DFT_FMA_OPT`;
   - mbfhe `spqlios-fma`.

3. Separate algorithm and backend claims:
   - same-backend scalar-vs-MAT speedup supports algorithm claims;
   - cross-library absolute time supports implementation/backend claims only.

4. Full bootstrap profile:
   - after Stage 5, re-run profile breakdown:
     `external product`, `CMUX/NCMUX`, `RGSW_monomial_mul`, `sparse_mul`,
     extract, packing KS, HW reducing KS, memory/keygen.

5. Repro pack:
   - commit hash;
   - commands;
   - CPU flags;
   - raw logs;
   - parameter set;
   - build flags.

## Goal Sufficiency Assessment

The current project roadmap is sufficient if the objective is:

```text
evaluate whether MAT/shared-mask external product can accelerate 2025/686 SAB,
then integrate it through progressively larger bootstrapping stages.
```

It is not sufficient if interpreted as already proving final bootstrapping
speedup. Current evidence proves only:

- MAT external product is implemented and tested;
- MAT has same-backend scalar-vs-MAT advantage for `r=2/4`;
- MOSFHET and mbfhe MAT implementations are close when SIMD level is aligned;
- the bootstrapping hot path is not yet converted.

Required next milestone:

```text
Stage 5 sab_pvw_* context/API and small full bootstrapping correctness.
```

Only after Stage 5 and full `sab_pvw_*` integration can the work claim anything
about full bootstrapping acceleration.
