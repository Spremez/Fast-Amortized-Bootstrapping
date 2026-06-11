# Stage 8 Full Bootstrap Gain Separation

Date: 2026-06-11

## Objective

Separate three quantities before making any 686 bootstrapping acceleration
claim:

- same-backend algorithmic throughput gain: PVW full SAB versus repeated scalar
  SAB on the same backend and parameter shape;
- backend/SIMD gain: absolute timing changes caused by changing FFT/backend;
- implementation-variant gain: clear-elision versus the pre-variant PVW path.

Machine-readable table:

- `repro/stage8_full_bootstrap_gain_separation.csv`

## Same-Backend Algorithmic Gain

These are the primary full SAB throughput numbers because scalar repeated and
PVW use the same `spqlios` backend in each row.

| variant | backend | r | runs | reps/run | PVW mean us | scalar repeated mean us | speedup |
|---|---|---:|---:|---:|---:|---:|---:|
| pre-variant | spqlios | 2 | 3 | 2 | 19,266,121.667 | 22,848,639.333 | 1.188x |
| pre-variant | spqlios | 4 | 3 | 2 | 35,402,965.167 | 46,436,548.167 | 1.312x |
| clear-elision | spqlios | 2 | 3 | 2 | 18,684,294.000 | 23,642,989.000 | 1.269x |
| clear-elision | spqlios | 4 | 3 | 2 | 35,044,592.833 | 46,848,311.333 | 1.337x |

Interpretation:

- The current best same-backend full SAB throughput evidence is
  `1.269x` at `r=2` and `1.337x` at `r=4` after clear-elision.
- The clear-elision comparison is an engineering variant comparison across
  separate process campaigns and commits, not a strict paired A/B.

## Backend/SIMD Sensitivity

Backend changes alter absolute time for both scalar repeated and PVW. These
rows must not be counted as algorithmic gain.

| backend | r | PVW absolute gain vs pre spqlios | scalar absolute gain vs pre spqlios | speedup | relative speedup ratio |
|---|---:|---:|---:|---:|---:|
| spqlios_avx512 | 2 | 1.277x | 1.386x | 1.099x | 0.925x |
| spqlios_avx512 | 4 | 1.271x | 1.335x | 1.249x | 0.952x |
| ffnt | 2 | 0.516x | 0.502x | 1.218x | 1.025x |

Interpretation:

- AVX512 improves absolute time, but it improves scalar repeated even more than
  PVW in these measurements, reducing the relative PVW speedup.
- FFNT remains a portability smoke only; it is not used for performance claims.
- The strongest backend-separated algorithmic signal is therefore still the
  same-backend `spqlios` full SAB result, especially `r=4`.

## Claim Boundary

Supported engineering statement:

```text
On the WSL/Linux spqlios performance platform, the sab_pvw_* full-output SAB
path improves per-lane throughput over repeated scalar SAB for r=2 and r=4,
with the best recorded clear-elision engineering results at 1.269x and 1.337x.
Backend/SIMD changes are reported separately and are not counted as algorithmic
gain.
```

Not yet supported:

```text
The speedup is a paper-grade novel algorithmic contribution.
```

That requires Stage 9 literature/novelty analysis and stronger statistical
treatment of the benchmark and failure-rate evidence.
