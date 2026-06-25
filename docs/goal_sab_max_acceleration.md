# Goal: Maximize PVW/MAT-SAB Acceleration

Date: 2026-06-25

## Codex Goal

Starting from commit `b007c0c`, continue the PVW/MAT-SAB optimization path for
2025/686 sparse amortized bootstrapping without weakening the existing scalar
SAB baseline.

The final target is complete `sab_pvw_*` bootstrapping throughput, not an
isolated external-product microbenchmark. The work should maximize practical
speedup subject to correctness, noise, resource, and reproducibility gates. No
fixed speedup multiple is required; the accepted result is the best scoped,
evidence-backed implementation that survives the full validation loop.

## Current Foundation

The project already has a complete PVW/MAT-SAB path and repeated full-SAB
evidence.

| evidence | backend | r | status | result |
|---|---|---:|---|---|
| Stage 8/10 clear-elision | `spqlios` | 2 | accepted engineering evidence | `1.269x` throughput |
| Stage 8/10 clear-elision | `spqlios` | 4 | accepted engineering evidence | `1.337x` throughput |
| Stage 16 AVX512 MAT full SAB | `spqlios_avx512` | 2 | positive, explicit flag | mean `1.197x`, range `1.155x-1.248x` |
| Stage 16 AVX512 MAT full SAB | `spqlios_avx512` | 4 | positive, explicit flag | mean `1.281x`, range `1.231x-1.324x` |
| Stage 18 fused from-DFT-add | `spqlios_avx512` | 4 | neutral ablation | mean `1.285x`, not materially above Stage 16 |

Current conclusion:

```text
PVW/MAT-SAB exists and is correct for the tested target path.
The project has complete SAB speedup evidence, but not a multi-fold result.
The next work is to maximize the complete SAB path by moving above local MAT
micro-optimizations into SAB schedule, buffer, and layout optimization.
```

## Invariants

All later stages must preserve these rules:

- scalar `sab_rlwe_bootstrap` remains callable and comparable;
- new implementations stay behind explicit flags or `sab_pvw_*` entry points
  until promoted by full gates;
- same-backend comparisons are the primary algorithmic speedup evidence;
- backend/SIMD absolute gains are reported separately from algorithmic gains;
- correctness failures stop promotion immediately;
- neutral and negative ablations remain recorded;
- no isolated kernel result may be described as final bootstrapping
  acceleration.

## Claim Levels

Use these labels consistently in docs, hypothesis records, and reports.

| label | meaning | allowed claim |
|---|---|---|
| `[implementation exists]` | code or script exists behind an explicit gate | runnable candidate only |
| `[correctness supported]` | staged and target correctness gates pass | semantic compatibility under tested scope |
| `[performance smoke only]` | one-run or low-repetition timing evidence | direction finding only |
| `[statistically supported engineering claim]` | repeated full SAB A/B plus correctness/noise/resource gates | scoped engineering speedup |
| `[paper-ready claim pending literature/theory]` | strong experiments exist, but prior art or proof work remains | candidate paper contribution |
| `[paper-ready claim]` | literature, theory, correctness, noise, resource, and full SAB evidence align | scoped manuscript claim |

## Final Completion Standard

The project reaches the current goal only if all conditions below hold:

1. A promoted `sab_pvw_*` full bootstrapping path matches repeated scalar SAB
   output under the target parameter sets.
2. Multi-seed correctness and noise gates pass for promoted variants.
3. Complete bootstrapping benchmark evidence shows stable throughput gain over
   repeated scalar SAB under the same backend.
4. Scalar baseline behavior and benchmarkability remain intact.
5. Algorithmic gains and backend/SIMD gains are separated.
6. Key size, keygen time, memory peak, and scratch overhead are reported.
7. Reproducibility artifacts contain commit, command, backend, CPU flags, raw
   logs, summaries, and decisions.
8. Paper-level claims are made only after a literature/novelty audit.

## Immediate Direction

The next implementation loop starts at Stage 19:

```text
Stage 19: exact sparse schedule audit.
Stage 20: active-buffer/copyback fusion.
Stage 21: sub_a and polynomial rotation optimization.
Stage 22: MAT-aware AVX512 theoretical-limit audit.
Stage 23: CMUX/NCMUX schedule fusion.
Stage 24: conditional post-processing optimization.
Stage 25: correctness/noise/resource matrix.
Stage 26: parameter and branch generalization.
Stage 27: novelty and paper package.
```
