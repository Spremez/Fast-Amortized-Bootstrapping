# Stage122 Structured EP Arithmetic Model

Date: 2026-07-03

Stage122 checks selector-application arithmetic after the Stage121
conversion gate. The dense reference evaluates all `r(r+1)` lane-row
external-product terms. The structured vector-shared variant evaluates
only two terms per lane: the lane-specific shared object and the lane
body object. Equality is required at the decrypted phase, not at the
ciphertext coefficient level, because masks differ between dense and
vector-shared objects.

The exact DFT gate computes the same structured EP by multiplying digit
polynomials and ciphertext mask/body polynomials in the frequency domain
and then converting back.

## Arithmetic Rows

| r | N | seed | dense/structured mismatches | coeff/DFT mismatches | noise violations | negative failures | EP ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 0 | 0 | 0 | 0 | 64 | 1.500000 |
| 2 | 32 | 1 | 0 | 0 | 0 | 62 | 1.500000 |
| 2 | 32 | 2 | 0 | 0 | 0 | 63 | 1.500000 |
| 2 | 32 | 3 | 0 | 0 | 0 | 64 | 1.500000 |
| 2 | 32 | 4 | 0 | 0 | 0 | 60 | 1.500000 |
| 2 | 64 | 0 | 0 | 0 | 0 | 127 | 1.500000 |
| 2 | 64 | 1 | 0 | 0 | 0 | 126 | 1.500000 |
| 2 | 64 | 2 | 0 | 0 | 0 | 127 | 1.500000 |
| 2 | 64 | 3 | 0 | 0 | 0 | 123 | 1.500000 |
| 2 | 64 | 4 | 0 | 0 | 0 | 128 | 1.500000 |
| 4 | 32 | 0 | 0 | 0 | 0 | 126 | 2.500000 |
| 4 | 32 | 1 | 0 | 0 | 0 | 127 | 2.500000 |
| 4 | 32 | 2 | 0 | 0 | 0 | 122 | 2.500000 |
| 4 | 32 | 3 | 0 | 0 | 0 | 126 | 2.500000 |
| 4 | 32 | 4 | 0 | 0 | 0 | 127 | 2.500000 |
| 4 | 64 | 0 | 0 | 0 | 0 | 254 | 2.500000 |
| 4 | 64 | 1 | 0 | 0 | 0 | 254 | 2.500000 |
| 4 | 64 | 2 | 0 | 0 | 0 | 249 | 2.500000 |
| 4 | 64 | 3 | 0 | 0 | 0 | 256 | 2.500000 |
| 4 | 64 | 4 | 0 | 0 | 0 | 256 | 2.500000 |
| 6 | 32 | 0 | 0 | 0 | 0 | 191 | 3.500000 |
| 6 | 32 | 1 | 0 | 0 | 0 | 191 | 3.500000 |
| 6 | 32 | 2 | 0 | 0 | 0 | 189 | 3.500000 |
| 6 | 32 | 3 | 0 | 0 | 0 | 188 | 3.500000 |
| 6 | 32 | 4 | 0 | 0 | 0 | 189 | 3.500000 |
| 6 | 64 | 0 | 0 | 0 | 0 | 380 | 3.500000 |
| 6 | 64 | 1 | 0 | 0 | 0 | 384 | 3.500000 |
| 6 | 64 | 2 | 0 | 0 | 0 | 380 | 3.500000 |
| 6 | 64 | 3 | 0 | 0 | 0 | 381 | 3.500000 |
| 6 | 64 | 4 | 0 | 0 | 0 | 383 | 3.500000 |

## Layout Rows

| r | N | dense EP terms | structured EP terms | EP ratio | dense selector polys | structured selector polys | selector ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 32 | 6 | 4 | 1.500000 | 9 | 8 | 1.125000 |
| 2 | 64 | 6 | 4 | 1.500000 | 9 | 8 | 1.125000 |
| 4 | 32 | 20 | 8 | 2.500000 | 25 | 16 | 1.562500 |
| 4 | 64 | 20 | 8 | 2.500000 | 25 | 16 | 1.562500 |
| 6 | 32 | 42 | 12 | 3.500000 | 49 | 24 | 2.041667 |
| 6 | 64 | 42 | 12 | 3.500000 | 49 | 24 | 2.041667 |

## Boundary

This gate does not prove production torus scaling, floating FFT roundoff,
gadget decomposition, real key generation, AVX512 performance, SAB
schedule compatibility, or complete `T_bootstrap/r` acceleration.
