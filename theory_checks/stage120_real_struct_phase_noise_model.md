# Stage120 Real Struct Phase/Noise Model

Date: 2026-07-03

Stage120 replaces scalar toy equations with actual C structs containing
polynomial arrays. Each lane has two RLWE-like ciphertext objects:
vector-shared and body. Each object contains mask and body polynomials.
Phase uses negacyclic multiplication `body - mask * secret`.

This is still not MOSFHET integration: coefficients are signed small
integers, not torus ciphertexts with production FFT/DFT arithmetic.

## Phase Summary

| r | N | seed | mismatches | max noise | max bound | violations |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 0 | 0 | 6 | 6 | 0 |
| 2 | 32 | 1 | 0 | 6 | 6 | 0 |
| 2 | 32 | 2 | 0 | 6 | 6 | 0 |
| 2 | 32 | 3 | 0 | 6 | 6 | 0 |
| 2 | 32 | 4 | 0 | 6 | 6 | 0 |
| 2 | 64 | 0 | 0 | 6 | 6 | 0 |
| 2 | 64 | 1 | 0 | 6 | 6 | 0 |
| 2 | 64 | 2 | 0 | 6 | 6 | 0 |
| 2 | 64 | 3 | 0 | 6 | 6 | 0 |
| 2 | 64 | 4 | 0 | 6 | 6 | 0 |
| 4 | 32 | 0 | 0 | 6 | 6 | 0 |
| 4 | 32 | 1 | 0 | 6 | 6 | 0 |
| 4 | 32 | 2 | 0 | 6 | 6 | 0 |
| 4 | 32 | 3 | 0 | 6 | 6 | 0 |
| 4 | 32 | 4 | 0 | 6 | 6 | 0 |
| 4 | 64 | 0 | 0 | 6 | 6 | 0 |
| 4 | 64 | 1 | 0 | 6 | 6 | 0 |
| 4 | 64 | 2 | 0 | 6 | 6 | 0 |
| 4 | 64 | 3 | 0 | 6 | 6 | 0 |
| 4 | 64 | 4 | 0 | 6 | 6 | 0 |
| 6 | 32 | 0 | 0 | 6 | 6 | 0 |
| 6 | 32 | 1 | 0 | 6 | 6 | 0 |
| 6 | 32 | 2 | 0 | 6 | 6 | 0 |
| 6 | 32 | 3 | 0 | 6 | 6 | 0 |
| 6 | 32 | 4 | 0 | 6 | 6 | 0 |
| 6 | 64 | 0 | 0 | 6 | 6 | 0 |
| 6 | 64 | 1 | 0 | 6 | 6 | 0 |
| 6 | 64 | 2 | 0 | 6 | 6 | 0 |
| 6 | 64 | 3 | 0 | 6 | 6 | 0 |
| 6 | 64 | 4 | 0 | 6 | 6 | 0 |

## Layout Summary

| r | N | dense terms | vector terms | vector/dense poly ratio | requested bytes |
|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 9 | 4 | 0.666667 | 2768 |
| 2 | 64 | 9 | 4 | 0.666667 | 5328 |
| 4 | 32 | 25 | 8 | 0.533333 | 5488 |
| 4 | 64 | 25 | 8 | 0.533333 | 10608 |
| 6 | 32 | 49 | 12 | 0.428571 | 8208 |
| 6 | 64 | 49 | 12 | 0.428571 | 15888 |
