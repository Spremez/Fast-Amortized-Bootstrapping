# Stage 9 Novelty Scan

Date: 2026-06-11

## Objective

Decide whether the current `sab_pvw_*` result should be framed as an
engineering optimization, a systems contribution, or a defensible algorithmic
paper contribution.

This is an initial scan, not a final related-work section. Broad novelty claims
remain unsafe until the cited papers are read at the algorithm-step level.

Machine-readable matrix:

- `repro/stage9_literature_matrix.csv`

## Proposed Delta

Target protocol:

- 2025/686 sparse amortized bootstrapping, keeping scalar SAB unchanged.

Implemented delta:

- add a `sab_pvw_*` path that batches multiple independent LUT/SAB lanes using
  PVW/MAT_TRGSW shared-mask multi-body external products;
- evaluate full-output SAB throughput against repeated scalar SAB;
- report backend/SIMD effects separately from same-backend algorithmic speedup.

Current evidence:

- best same-backend full SAB speedup after clear-elision: `1.269x` at `r=2`,
  `1.337x` at `r=4`;
- `r=2` clear-elision deterministic noise/correctness: `50` seeds,
  `204800` points, PVW/scalar/pair failures all `0`;
- `r=4` clear-elision deterministic noise/correctness: `50` seeds,
  `409600` points, PVW/scalar/pair failures all `0`.

## Initial Literature Map

| work | relationship | novelty risk |
|---|---|---|
| 2025/686, Fast amortized bootstrapping with small keys and polynomial noise overhead | target protocol and scalar implementation baseline | baseline, not novelty |
| 2013 PVW packed ciphertexts | establishes PVW-style packed/SIMD LWE direction | high risk for broad PVW packing claims |
| 2018 ring packing and amortized FHEW | foundational amortized FHEW bootstrapping | medium risk for generic amortized batching claims |
| 2023 Batch Bootstrapping I | SIMD bootstrapping framework in polynomial modulus | medium-high risk for broad SIMD bootstrapping claims |
| 2023 Amortized Bootstrapping Revisited | implemented predecessor in the amortized bootstrapping line | medium risk; check for packed external-product batching |
| 2024 ring-automorphism amortized FHEW | acceleration through a different mathematical axis | medium risk for generic acceleration claims |
| 2025/696 incomplete NTT | recent transform-level amortized bootstrapping acceleration | medium risk; orthogonal backend/transform axis |

## Claim Boundary

Safe engineering claim:

```text
We implemented and evaluated a PVW/MAT_TRGSW shared-mask multi-body
sab_pvw_* path for the 2025/686 sparse amortized bootstrapping codebase. On
the WSL/Linux spqlios platform, the full-output SAB path improves same-backend
per-lane throughput over repeated scalar SAB for r=2 and r=4, while preserving
the scalar baseline.
```

Unsafe until further evidence:

```text
PVW packing, multi-LUT/multi-output bootstrapping, or amortized bootstrapping
itself is new.
```

Potential paper-level claim, still unverified:

```text
The specific integration of PVW/MAT_TRGSW shared-mask multi-body external
products into the 2025/686 sparse polynomial multiplication / SAB hot path is
new and gives a measurable full-bootstrapping throughput gain.
```

Required before upgrading that claim:

- read 2025/686, 2023/014, 2025/696, Batch Bootstrapping I/II, and ring-packing
  papers at algorithm-step level;
- verify whether any work already batches independent LUT/SAB lanes through a
  shared-mask matrix external product inside a sparse amortized bootstrapping
  hot path;
- add a related-work table that distinguishes protocol-level amortization,
  PVW/SIMD packing, transform/backend acceleration, and implementation-level
  external-product batching;
- run citation-support verification for every claim intended for a paper draft.

## Stage 9 Next Decisions

- `r=4` 50-seed noise evidence is now available. If the project targets a
  paper claim, the next evidence upgrade should be statistical treatment and
  stage-level noise probes rather than another small deterministic sweep.
- Initial statistical treatment is recorded in
  `docs/stage9_statistical_evidence.md`. It supports the engineering
  correctness/noise gate, but not a paper-grade failure-rate claim.
- Decide whether Stage 9 should target a paper contribution or a rigorous
  engineering report. The current evidence supports the latter; the former
  requires deeper related-work exclusion and statistical treatment.
