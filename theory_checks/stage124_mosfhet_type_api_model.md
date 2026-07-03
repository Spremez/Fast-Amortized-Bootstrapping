# Stage124 MOSFHET Type/API Model

Date: 2026-07-03

Stage124 defines the first MOSFHET-adjacent type/API skeleton for the
vector-shared route selected by Stage119 and exercised arithmetically by
Stage122/123. The skeleton deliberately does not modify MOSFHET headers or
the SAB hot path.

For k=1, the current PVW accumulator stores `k+r = 1+r` polynomials.
The vector-shared accumulator stores one lane-local mask/body ciphertext
per lane, or `r(k+1) = 2r` polynomials. This is an accumulator overhead.
The selector side is where the structured route must win: current dense
`MAT_TRGSW_DFT` storage is `T(k+r)^2`, while the compact vector-shared
selector skeleton stores `2Tr(k+1)` DFT polynomials.

## API Rows

| backend | r | N | T | k | component failures | metadata failures | coverage failures | roundtrip mismatches | max gap | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 1024 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 4 | 1024 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 6 | 1024 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 2 | 2048 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 4 | 2048 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |
| spqlios | 6 | 2048 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 1024 | PASS_TYPE_API_SKELETON |

## Layout Rows

| r | N | T | current acc | vector acc | acc overhead | current selector | vector selector | selector ratio | current total | vector total | total ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1024 | 7 | 3 | 4 | 1.333333 | 63 | 56 | 1.125000 | 66 | 60 | 1.100000 |
| 4 | 1024 | 7 | 5 | 8 | 1.600000 | 175 | 112 | 1.562500 | 180 | 120 | 1.500000 |
| 6 | 1024 | 7 | 7 | 12 | 1.714286 | 343 | 168 | 2.041667 | 350 | 180 | 1.944444 |
| 2 | 2048 | 7 | 3 | 4 | 1.333333 | 63 | 56 | 1.125000 | 66 | 60 | 1.100000 |
| 4 | 2048 | 7 | 5 | 8 | 1.600000 | 175 | 112 | 1.562500 | 180 | 120 | 1.500000 |
| 6 | 2048 | 7 | 7 | 12 | 1.714286 | 343 | 168 | 2.041667 | 350 | 180 | 1.944444 |

## Boundary

This stage is a type/API skeleton gate. It does not prove selector
encryption, gadget decomposition, noise growth, AVX512 performance, SAB
schedule compatibility, extraction/key switching, or complete
`T_bootstrap/r` acceleration.
