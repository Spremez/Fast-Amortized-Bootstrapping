# Stage 27 Related-Work Refresh Log

Date: 2026-06-25

## Goal

Refresh the Stage 27 source-access and novelty-risk gate after the Stage 26
5-run/5-seed added-binary parameter matrix. The target is not a broad survey;
it is a claim-boundary check for the specific delta in this project:

```text
PVW/MAT shared-mask multi-body external products integrated into the
2025/686 sparse amortized bootstrapping schedule, with active-buffer/copyback
fusion and complete-SAB throughput evidence.
```

## Search Axes

- baseline algorithm plus changed module:
  `2025/686`, sparse amortized bootstrapping, sparse polynomial
  multiplication, `sab_pvw_*`;
- shared-mask/common-mask multi-body TFHE:
  common mask, multiple bodies, Matrix-LWE, distinct LUTs, external products;
- adjacent amortized-bootstrapping accelerators:
  incomplete NTT, NTT-based homomorphic polynomial multiplication,
  amortized bootstrapping revisited;
- implementation and backend boundary:
  AVX512, backend fairness, complete-SAB throughput versus isolated kernel
  speed.

## Source Access Refresh

| work | refreshed source status | evidence obtained | claim effect |
|---|---|---|---|
| 2025/686 FAB | still partial | author page, GitHub README, ACM/ResearchGate metadata are accessible; ePrint/ACM PDF access remains blocked in this environment | base algorithm and implementation lineage are anchored, but theorem/algorithm/remark-number citation remains blocked |
| 2025/2112 Sharing the Mask | stronger than before | ResearchGate public full-text and DBLP metadata expose common-mask ciphertexts, shared mask, multiple bodies, distinct LUTs, and CM bootstrapping | blocks any claim that this project invents shared-mask or multi-body TFHE batching |
| 2025/696 incomplete NTT | full ePrint PDF accessible | paper and repository show a different incomplete-NTT amortized-bootstrapping acceleration path | adjacent competitor/context, not direct PVW/MAT-SAB prior art |
| GPVL23 amortized bootstrapping revisited | public PDF accessible | establishes earlier amortized bootstrapping implementation lineage and polynomial-multiplication bottleneck context | background for amortized bootstrapping, not the specific PVW/MAT-SAB delta |
| 2026 bootstrapping optimization survey | accessible secondary source | references recent bootstrapping optimization literature | secondary context only; not enough for novelty or performance claims |

## Novelty-Risk Map

| zone | assessment |
|---|---|
| same idea already exists | common-mask/shared-mask ciphertexts with multiple bodies and TFHE-style bootstrapping exist in 2025/2112 |
| adjacent work exists | incomplete-NTT amortized bootstrapping and GPVL23-style amortized bootstrapping optimize different polynomial-multiplication or NTT paths |
| scoped local delta | current project integrates PVW/MAT multi-body batching into the 2025/686 sparse SAB schedule and validates active-buffer, MAT-AVX512, noise/resource, and complete-SAB performance under tested binary parameters |
| no reliable evidence found | no public full-text evidence yet proves that the exact `sab_pvw_*` integration and active-buffer schedule fusion is already described for 2025/686; this remains an engineering novelty candidate only until full-paper review |

## Updated Claim Boundary

Allowed:

```text
Engineering/systems claim: under scoped binary parameters and the recorded
backend, the explicit PVW/MAT-SAB path batches multiple independent LUT/SAB
lanes and improves complete-SAB throughput over repeated scalar SAB while
preserving tested correctness/noise gates.
```

Blocked:

```text
Novel shared-mask batching.
Theoretical-optimal MAT-AVX512 implementation.
Non-binary PVW-SAB support.
All-parameter or multi-fold SAB acceleration.
Theorem-level claims about 2025/686 internals before the full paper is
manually inspected.
```

## Decision

Status:

```text
RELATED_WORK_REFRESH_COMPLETED
SAFE_ENGINEERING_CLAIM_STRENGTHENED
NOVELTY_CLAIM_STILL_BLOCKED
FAB686_FULL_TEXT_STILL_REQUIRED_FOR_MANUSCRIPT
```

Next work is to assemble the final manuscript evidence package from the current
claim support matrix, or manually obtain and inspect the full 2025/686 paper if
the paper draft needs theorem/algorithm-level citations.
