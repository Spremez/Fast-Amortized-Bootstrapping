# Stage126 Compact Selector Encryption/Noise Model

Date: 2026-07-03

Stage126 adds a deterministic encryption/noise simulator to the compact
selector route. Each compact selector row is represented as
`body = mask * secret + gadget + noise` using MOSFHET polynomial
operations. The gate verifies the external-product decrypted phase against
a coefficient-domain clean reference plus exact modeled noise, then checks
the same computation through production SPQLIOS DFT.

This is not a probabilistic failure-rate proof. It is the finite gate
needed before implementing an isolated compact external-product kernel.

## Noise Rows

| backend | r | N | T | seed | coeff mismatches | DFT mismatches | model mismatches | bound violations | negative failures | max DFT gap | max noise | bound | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 512 | 7 | 0 | 0 | 0 | 0 | 0 | 1024 | 10810 | 8560 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 2 | 512 | 7 | 1 | 0 | 0 | 0 | 0 | 1024 | 11789 | 8789 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 4 | 512 | 7 | 0 | 0 | 0 | 0 | 0 | 2048 | 9761 | 10794 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 4 | 512 | 7 | 1 | 0 | 0 | 0 | 0 | 2048 | 13844 | 8789 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 6 | 512 | 7 | 0 | 0 | 0 | 0 | 0 | 3072 | 11488 | 10794 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 6 | 512 | 7 | 1 | 0 | 0 | 0 | 0 | 3072 | 11755 | 8892 | 458752 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 2 | 1024 | 7 | 0 | 0 | 0 | 0 | 0 | 2048 | 12235 | 13022 | 917504 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 4 | 1024 | 7 | 0 | 0 | 0 | 0 | 0 | 4096 | 11107 | 13022 | 917504 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |
| spqlios | 6 | 1024 | 7 | 0 | 0 | 0 | 0 | 0 | 6144 | 14449 | 13022 | 917504 | 131072 | PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE |

## Layout Rows

| r | N | per-lane noise ratio | selector ratio | status |
|---:|---:|---:|---:|---|
| 2 | 512 | 1.500000 | 1.125000 | PASS_NOISE_LAYOUT_MODEL |
| 2 | 512 | 1.500000 | 1.125000 | PASS_NOISE_LAYOUT_MODEL |
| 4 | 512 | 2.500000 | 1.562500 | PASS_NOISE_LAYOUT_MODEL |
| 4 | 512 | 2.500000 | 1.562500 | PASS_NOISE_LAYOUT_MODEL |
| 6 | 512 | 3.500000 | 2.041667 | PASS_NOISE_LAYOUT_MODEL |
| 6 | 512 | 3.500000 | 2.041667 | PASS_NOISE_LAYOUT_MODEL |
| 2 | 1024 | 1.500000 | 1.125000 | PASS_NOISE_LAYOUT_MODEL |
| 4 | 1024 | 2.500000 | 1.562500 | PASS_NOISE_LAYOUT_MODEL |
| 6 | 1024 | 3.500000 | 2.041667 | PASS_NOISE_LAYOUT_MODEL |

## Boundary

This gate does not prove randomized cryptographic failure rate, full SAB
noise accumulation, AVX512 performance, schedule compatibility, extract/KS
behavior, or complete `T_bootstrap/r` acceleration.
