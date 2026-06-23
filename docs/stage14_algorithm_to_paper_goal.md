# Stage 14 Algorithm-to-Paper Goal

Date: 2026-06-23

## Direct Answer: MAT AVX512 Status

The MAT external-product AVX512 implementation is not yet complete enough to
call "fully optimized" or "paper-ready".

What is implemented:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
k=1
l=1
r in {2,4}
```

The v2 small-r path uses direct AVX512 complex FMA code and keeps one DFT
coefficient block's output accumulators in ZMM registers. It removes the first
variant's pointer-array output loop and has passed staged and target correctness
gates.

What is supported by evidence:

| item | status | evidence |
|---|---:|---|
| default AVX512 staged gate | supported with small-N skip policy | `docs/stage12_avx512_gate_and_v2_kernel_log.md` |
| v2 `r=2/r=4` staged correctness | supported | `repro/stage12_avx512_smallr_v2_kernel/main.log` |
| v2 target full correctness | supported | `repro/stage12_avx512_smallr_v2_target_full/main.log` |
| v2 isolated MAT speedup | engineering-positive | `r=2 1.226x`, `r=4 1.584x` |
| v2 full-output MAT speedup | engineering-positive | `r=2 1.449x`, `r=4 1.481x` |
| v2 full SAB speedup | smoke only | `r=2 1.137x`, `r=4 1.253x` |

Why it is not complete:

- it covers only `k=1,l=1,r=2/4`;
- it is explicit-flag only and not the default path;
- it has no AVX2/FMA small-r specialization;
- it has not been compared with compiler-generated assembly, perf counters,
  cache misses, or memory-bandwidth counters;
- it does not prove full SAB speedup beyond the accepted Stage 10 result;
- it does not reduce the dense `(k+r)^2*l` MAT arithmetic count;
- it does not address the dominant `bootstrap_wo_extract` body after Stage 13.

Current conclusion:

```text
[implementation exists]
[isolated kernel evidence positive]
[full SAB final acceleration not established]
[paper-ready optimization claim not supported]
```

## Current Project State

Accepted engineering result:

```text
clear-elision sab_pvw full-output SAB
backend: WSL/Linux FFT_LIB=spqlios
scope: binary SET_2_3_2048
r=2: 1.269x full SAB throughput over repeated scalar SAB
r=4: 1.337x full SAB throughput over repeated scalar SAB
50-seed final-output correctness/noise gates passed for r=2 and r=4
```

Stage 13 post-processing profile:

| r | bootstrap_wo_extract | direct_extract | packing KS | HW-KS |
|---:|---:|---:|---:|---:|
| 2 | 99.045% | 0.062% | 0.891% | 0.001% |
| 4 | 98.519% | 0.380% | 1.099% | 0.001% |

This means the next optimization target is not extraction alone. The target is
the PVW blind-rotation body:

```text
setup_tv_xb -> blind_rotate -> sparse_mul
  -> RGSW_monomial_mul
    -> CMUX/NCMUX
      -> MAT external product
```

## Full Future Algorithm Roadmap

### Stage 14: PVW Body Profile

Goal:

```text
Measure the internal cost of PVW bootstrap_wo_extract and sparse blind rotation.
```

Required counters:

- setup_tv_xb;
- blind_rotate;
- sparse_mul;
- RGSW_monomial_mul;
- CMUX;
- NCMUX;
- MAT external-product call;
- sub_a;
- copy-back after odd `r_prec`.

Gate:

- profile build must pass `SAB_PVW_BENCH` correctness;
- profile must produce parseable CSV for `r=2` and `r=4`;
- default non-profile build remains unchanged.

Decision output:

```text
If CMUX/MAT dominates: optimize MAT or CMUX fusion.
If sub_a/copy dominates: optimize rotations and memory layout.
If setup dominates unexpectedly: optimize LUT/input setup.
```

### Stage 15: CMUX/NCMUX Fusion

Goal:

```text
Reduce per-CMUX overhead around MAT external product without changing semantics.
```

Candidate changes:

- fuse `pvmtmlwe_sub`, MAT product, inverse DFT, and add into one scratch-aware
  CMUX helper;
- avoid redundant temporary clears and copies;
- specialize `NCMUX` so automorphism output feeds CMUX scratch without extra
  materialization when possible;
- split `r=2` and `r=4` CMUX paths if profile confirms dispatch overhead.

Gates:

- staged CMUX/NCMUX lane equivalence for `r=1/2/4`;
- target full correctness;
- no increase in noise relative to Stage 10/13 gates;
- full SAB A/B smoke before three-run sweep.

### Stage 16: SAB-specific RGSW Monomial/Sparse Fusion

Goal:

```text
Exploit the binary monomial selector structure in 2025/686 SAB to reduce
loop-level overhead across r_prec butterfly stages.
```

Candidate changes:

- fuse `RGSW_monomial_mul` and `sub_a` per sparse step;
- reduce array ping-pong copies across `r_prec`;
- precompute index schedules for `power=2^bit`;
- avoid recomputing `in_N - power + j` and rotation metadata in hot loops;
- create a batched butterfly schedule object for target `in_N=2048,r_prec=7`.

Gates:

- isolated RGSW-monomial lane equivalence;
- sparse_mul lane equivalence;
- bootstrap_wo_extract lane equivalence;
- target full correctness;
- profile evidence that call count or copy traffic drops.

### Stage 17: MAT External Product Completion

Goal:

```text
Decide whether MAT AVX512 should become a supported optimization or remain an
experimental kernel.
```

Required work:

- r=2/r=4 three-process full SAB sweep under `spqlios_avx512`;
- perf-counter audit for cycles, instructions, cache misses, and bandwidth;
- inspect generated assembly for generic path vs v2 path;
- compare direct v2 with compiler-unrolled C fallback;
- consider AVX2/FMA specialized path for non-AVX512 systems;
- document when small-r specialization is enabled or rejected.

Promotion gate:

```text
Do not enable by default unless same-backend full SAB speedup is stable and
does not regress correctness/noise/resource gates.
```

### Stage 18: Direct-to-Packing KS Only If Justified

Goal:

```text
Remove the remaining per-lane TLWE materialization only if Stage 14+15 show the
tail is large enough to matter.
```

Stage 13 says this tail is about 1% at the target shape, so this is lower
priority than sparse blind-rotation fusion.

### Stage 19: Correctness, Noise, Resource Matrix

Goal:

```text
Move from engineering smoke to robust engineering evidence.
```

Required matrix:

- `r in {1,2,4}` negative/control/scaling;
- `spqlios` and `spqlios_avx512` backend separation;
- target correctness for every promoted variant;
- deterministic seed sweeps for final-output noise;
- stage-level noise for changed arithmetic boundaries;
- key size, keygen time, RSS, scratch memory;
- failure logs preserved.

### Stage 20: Parameter and Branch Coverage

Goal:

```text
Decide whether the contribution is scoped to binary SET_2_3_2048 or generalizes.
```

Required before broad claim:

- additional binary parameter sets;
- ternary/include-zero branches;
- gaussian/sparse-generic branches if claimed;
- large `r` behavior and failure modes.

### Stage 21: Literature and Novelty Audit

Goal:

```text
Convert engineering evidence into a defensible paper contribution boundary.
```

Required:

- read 2025/686 at algorithm-step level;
- read PVW packing and ring-packing/amortized bootstrapping related work;
- compare against batch/SIMD bootstrapping and packed ciphertext literature;
- mark broad PVW packing as prior art;
- claim only the supported SAB-specific integration or fused sparse scheduling.

### Stage 22: Paper Drafting

Paper-ready only when all are true:

- construction is formalized;
- complexity theorem or proposition is written;
- correctness/noise argument is written;
- benchmark matrix has repeated runs and confidence summaries;
- related-work matrix is citation-verified;
- limitations are explicit.

Expected paper structure:

```text
1. Introduction and Contributions
2. Background: 2025/686 SAB and PVW/MAT_TRGSW
3. Baseline Cost Model
4. PVW/MAT-SAB Construction
5. SAB-specific Optimizations
6. Correctness and Noise Analysis
7. Implementation and Evaluation
8. Related Work
9. Limitations
```

## Stage 14 Execution Entry

The next concrete execution step is:

```text
Add SAB_PVW_BODY_PROFILE and run r=2/r=4 one-run profile gates.
```

This is required before changing the blind-rotation body because Stage 13
already showed post-processing is not the main target.

## Stage 14 Execution Result

Implemented:

- `SAB_PVW_BODY_PROFILE=true` compile-time profile switch;
- inclusive counters for setup, blind rotate, sparse multiply, RGSW monomial,
  CMUX/NCMUX, MAT external product, `sub_a`, and copy-back;
- `scripts/run_stage14_body_profile.sh`;
- `docs/stage14_body_profile_log.md`;
- `experiments/stage14_body_profile_validation_plan.md`;
- `repro/stage14_body_profile_summary.csv`.

Target profile smokes passed for `r=2` and `r=4` on:

```text
FFT_LIB=spqlios
KEY=BINARY
PARAM=SET_2_3_2048
SAB_PVW_BENCH_REPS=1
```

The structural count was verified:

```text
MAT external products = (h + 1) * r_prec * in_N
                      = 40 * 7 * 2048
                      = 573440
```

Timed sample percentages:

| r | body/full us | CMUX | MAT EP | CMUX minus MAT EP | interpretation |
|---:|---:|---:|---:|---:|---|
| 2 | 22,922,300 | 95.546% | 43.805% | 51.741% | CMUX wrapper/schedule work is larger than MAT EP alone |
| 4 | 42,393,097 | 95.988% | 47.199% | 48.789% | MAT grows with lane count, but not enough to be the only target |

Decision:

```text
Stage 15 should start with fused CMUX/NCMUX and scratch-aware dataflow.
Stage 16 should reduce RGSW-monomial copy/schedule overhead.
Stage 17 should complete AVX512 MAT only after the SAB body target is stable.
```

The Stage 14 data does not change the current paper-claim boundary:

```text
current claim: engineering PVW/MAT-SAB path with accepted Stage 10 throughput
               improvement and Stage 14 profile-guided next targets
not supported: completed AVX512 MAT implementation or multi-fold SAB speedup
```
