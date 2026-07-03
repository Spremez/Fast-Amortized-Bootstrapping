# Stage121 Vector-Shared DFT/Conversion Model

Date: 2026-07-03

Stage121 checks whether the vector-shared lane-local object from Stage120
can cross a frequency-domain conversion boundary without changing its
phase semantics. The prototype uses exact modular evaluation at the
roots of `X^N + 1` modulo 12289. It is a semantic conversion gate,
not a production SPQLIOS/AVX512 performance gate.

For each lane q, coefficient-domain phase is

```text
phase_q = b_q - a_q * s_q mod (X^N + 1).
```

The conversion gate computes

```text
DFT(phase_q) = DFT(b_q) - DFT(a_q) * DFT(s_q),
phase_q' = InvDFT(DFT(phase_q)).
```

The gate passes only when `phase_q' == phase_q` for clean and noisy
shared/body objects across all tested r, N, and seeds.

## Conversion Rows

| r | N | seed | root | roundtrip | phase | noisy phase | noise violations | max noise | bound |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 32 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 32 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 32 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 32 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 64 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 64 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 64 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 64 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 2 | 64 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 32 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 32 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 32 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 32 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 32 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 64 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 64 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 64 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 64 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 4 | 64 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 32 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 32 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 32 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 32 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 32 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 64 | 0 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 64 | 1 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 64 | 2 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 64 | 3 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |
| 6 | 64 | 4 | PASS_ROOT | 0 | 0 | 0 | 0 | 6 | 6 |

## Layout Rows

| r | N | dense DFT polys | vector DFT polys | ratio | conversion input polys | requested bytes |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 12 | 8 | 0.666667 | 10 | 2768 |
| 2 | 64 | 12 | 8 | 0.666667 | 10 | 5328 |
| 4 | 32 | 30 | 16 | 0.533333 | 20 | 5488 |
| 4 | 64 | 30 | 16 | 0.533333 | 20 | 10608 |
| 6 | 32 | 56 | 24 | 0.428571 | 30 | 8208 |
| 6 | 64 | 56 | 24 | 0.428571 | 30 | 15888 |

## Boundary

This gate does not prove production FFT roundoff, torus scaling, gadget
decomposition, AVX512 optimality, SAB schedule compatibility, or
complete `T_bootstrap/r` acceleration. It only permits the next
structured external-product arithmetic prototype.
