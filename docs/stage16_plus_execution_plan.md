# Stage 16+ Execution Plan and Audit Gates

Date: 2026-06-25

Update:

```text
Stage 16 through Stage 18 have now been executed and recorded. For the active
Stage 19+ roadmap after the Stage 18 neutral fused-from-DFT-add result, use
docs/goal_sab_max_acceleration.md, docs/roadmap_stage19_plus.md, and
docs/loop_engineering.md as the controlling plan.
```

## Overall Goal

Complete the PVW/MAT-SAB optimization path for 2025/686 without weakening the
existing scalar SAB baseline.

The project is now past the point where isolated MAT microbenchmarks are enough.
All later stages must decide whether a claim is:

```text
[implementation exists]
[correctness supported]
[performance smoke only]
[statistically supported engineering claim]
[paper-ready claim pending literature/theory]
```

No later stage may claim final bootstrapping acceleration unless the complete
`sab_pvw_*` bootstrapping path beats repeated scalar `sab_rlwe_bootstrap` under
the same backend, target parameter set, and correctness/noise protocol.

## Current State Before Stage 16

Accepted engineering baseline:

```text
Backend: WSL/Linux spqlios
Parameter: BINARY SET_2_3_2048
r=2 clear-elision PVW/MAT-SAB: 1.269x throughput speedup
r=4 clear-elision PVW/MAT-SAB: 1.337x throughput speedup
50-seed correctness/noise campaigns passed for r=2 and r=4
```

Stage 15 AVX512 MAT state:

```text
Backend: spqlios_avx512
Flag: MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
Shape: k=1,l=1,r in {2,4}
MAT full-output speedups: r=2 1.416x, r=4 1.471x
Full SAB evidence: one-run smoke only, r=2 1.265x, r=4 1.356x
```

Stage 14 body profile showed the full-body target:

```text
MAT external products = 573440
CMUX ~= 95%-96% of PVW body time
MAT EP ~= 44%-47% of PVW body time
CMUX wrapper/schedule work remains too large to ignore
```

Therefore the next stages are ordered as:

```text
Stage 16: Promote or reject Stage 15 AVX512 MAT at full SAB level.
Stage 17: Perf-counter and assembly audit of accepted hot functions.
Stage 18: CMUX/NCMUX scratch-aware fusion.
Stage 19: RGSW-monomial and sparse_mul schedule fusion.
Stage 20: Correctness/noise/resource matrix for promoted variants.
Stage 21: Parameter and branch coverage.
Stage 22: Literature/novelty audit.
Stage 23: Paper-ready theorem/experiment package.
```

## Stage 16: Full SAB AVX512 MAT Audit

Goal:

```text
Turn Stage 15 full SAB smoke into repeated complete-bootstrapping evidence.
```

Hypothesis:

```text
H1-refined: Under BINARY SET_2_3_2048 and spqlios_avx512, the FMA-accumulate
small-r MAT kernel improves complete sab_pvw_* throughput over repeated scalar
SAB for r=2 and r=4 because shared mask decomposition/DFT and full-output
conversion savings dominate the dense MAT addmul overhead.
```

Correctness gate:

- every run must print `SAB_PVW_BENCH correctness target_full Pass`;
- no partial or timed-out run may be included as accepted evidence;
- scalar baseline path must remain callable in the same benchmark binary.

Performance gate:

- minimum `runs=3` process-level runs for r=2 and r=4;
- same backend, same binary, same timing harness for PVW and repeated scalar;
- report mean speedup and min/max speedup;
- accepted only if every process run is positive and the mean is above 1.10x.

Failure handling:

- if any correctness run fails, stop and mark Stage 16 failed;
- if speedup is unstable or mean <= 1.10x, keep AVX512 MAT explicit-flag only;
- if r=4 regresses while r=2 passes, promote only r=2 and document r=4 as
  dense-MAT limited.

Artifacts:

- `scripts/run_stage16_full_sab_audit.sh`;
- `experiments/stage16_full_sab_audit_plan.md`;
- `repro/stage16_avx512_full_sab_audit_runs*/summary.csv`;
- `docs/stage16_full_sab_audit_log.md`.

## Stage 17: Perf-Counter and Assembly Audit

Goal:

```text
Separate algorithmic gain from backend/SIMD gain and locate the next true
runtime limiter.
```

Required measurements:

- cycles and instructions;
- IPC;
- branch misses;
- cache misses;
- AVX512 instruction presence;
- time split between MAT EP, CMUX wrapper, RGSW monomial, sparse_mul, setup,
  extract, packing KS, HW-KS.

Correctness gate:

- perf/profile builds must reproduce Stage 16 correctness;
- instrumentation must not be used for final latency claims unless explicitly
  labeled as instrumented.

Performance gate:

- explain whether speedup comes from fewer rows/DFT conversions, fewer writes,
  AVX512 FMA throughput, cache locality, or backend effects;
- no default promotion without a hot-path attribution.

Failure handling:

- if `perf` is unavailable under WSL, preserve the failed attempt and fall back
  to `objdump`, timed phase counters, and `/usr/bin/time -v`;
- if counters show memory-bound behavior, prioritize scratch/layout work over
  more FMA unrolling.

## Stage 18: CMUX/NCMUX Scratch-Aware Fusion

Goal:

```text
Reduce the non-MAT half of CMUX cost identified by Stage 14.
```

Candidate algorithm delta:

- create fused helpers that combine PVW subtraction, MAT external product,
  inverse DFT/output conversion, and add-back into a scratch-aware CMUX;
- avoid redundant clears/copies in the hot path;
- specialize NCMUX so automorphism/substitution output can feed CMUX scratch
  directly;
- keep scalar `CMUX` and existing `sab_rlwe_bootstrap` untouched.

Correctness gate:

- staged CMUX/NCMUX lane equivalence for r=1/2/4;
- RGSW monomial lane equivalence;
- target full `SET_2_3_2048` equivalence.

Performance gate:

- body profile must show CMUX wrapper-minus-MAT time decreases;
- complete full SAB speedup must improve or at least not regress Stage 16.

Failure handling:

- if fused CMUX improves microbench but not full SAB, keep it behind a flag;
- if noise changes, revert the fused path and record the failed boundary.

## Stage 19: RGSW-Monomial and Sparse Schedule Fusion

Goal:

```text
Move above individual CMUX calls and exploit the fixed SAB butterfly/sparse
schedule.
```

Candidate algorithm delta:

- precompute butterfly index schedules for `in_N=2048,r_prec=7`;
- fuse `RGSW_monomial_mul`, `sub_a`, and CMUX dispatch at the sparse step;
- remove ping-pong copies where the parity of `r_prec` is known;
- specialize binary `h=39,r_prec=7` target first.

Correctness gate:

- isolated sparse_mul lane equivalence;
- bootstrap_wo_extract lane equivalence;
- full-output target equivalence.

Performance gate:

- profile must show fewer schedule/copy/substitution costs;
- complete SAB speedup must beat Stage 16 by a practical margin.

Failure handling:

- if schedule fusion is correct but neutral, keep it as a documented negative
  ablation and return to MAT density reduction.

## Stage 20: Correctness, Noise, and Resource Matrix

Goal:

```text
Convert a promoted implementation into robust engineering evidence.
```

Required matrix:

- r in {1,2,4};
- backends `spqlios` and `spqlios_avx512`;
- target correctness;
- deterministic seed sweeps;
- final-output noise and stage-level noise;
- keygen time, key size, RSS, and scratch memory;
- raw logs for failures and negative runs.

Correctness/noise gate:

- failure count must not exceed scalar repeated SAB under the same seed range;
- noise gap must stay within the previously accepted bound unless a new proof
  justifies the change.

Performance gate:

- report latency, per-lane throughput, speedup, standard deviation, and
  resource overhead;
- separate algorithmic speedup from backend/SIMD speedup.

## Stage 21: Parameter and Branch Coverage

Goal:

```text
Define the exact scope of the contribution.
```

Required before broad claims:

- additional binary parameter sets;
- ternary/include-zero branch checks if claimed;
- r-scaling beyond {2,4} only if a non-dense MAT strategy exists;
- fallback behavior for non-AVX512 systems.

Gate:

- unsupported branches must be explicitly labeled out-of-scope;
- no general SAB claim may be made from only `BINARY SET_2_3_2048`.

## Stage 22: Literature and Novelty Audit

Goal:

```text
Prevent engineering work from being overstated as a new cryptographic idea.
```

Required:

- paper-techgraph of 2025/686 SAB algorithm steps;
- related-work matrix for PVW, MAT_TRGSW, packed bootstrapping, amortized
  bootstrapping, and SIMD/shared-mask external products;
- citation support bank for every novelty claim.

Gate:

- broad PVW/MAT batching is prior-art-risk until checked;
- only the SAB-specific integration, fusion, or complexity reduction supported
  by experiments may become a paper claim.

## Stage 23: Paper-Ready Package

Goal:

```text
Produce a defensible manuscript package, not just benchmark notes.
```

Required:

- formal algorithm description;
- correctness theorem or proposition;
- noise/security discussion for changed boundaries;
- asymptotic and measured complexity;
- repeated benchmark tables with statistical summaries;
- ablations and negative evidence;
- limitations and scoped claims.

Exit gate:

```text
The project is paper-ready only if the complete SAB benchmark, correctness,
noise, resource, theory, and literature gates all support the same scoped claim.
```

## Immediate Auto-Advance

The next command to run is:

```bash
STAGE16_FULL_SAB_RUNS=3 STAGE16_FULL_SAB_REPS=1 \
  bash scripts/run_stage16_full_sab_audit.sh
```

This closes the current evidence gap before deeper CMUX/sparse fusion work.
