# Stage 27 Full Related-Work Gate Log

Date: 2026-06-25

## Goal

Record whether the Stage 27 literature gate has enough source access to promote
paper claims, especially novelty claims around shared-mask/PVW/MAT batching for
SAB.

## Source Access Result

| work | access status | usable evidence | effect on claim |
|---|---|---|---|
| 2025/686 FAB | partial | author page abstract, GitHub metadata, ACM DOI metadata; direct ePrint/ACM PDF fetch returned 403 in this environment | enough to anchor the base SAB/code lineage, not enough for theorem-level citation checking |
| 2025/2112 Sharing the Mask | preliminary full text | public full-text page exposes abstract and relevant body text describing common-mask ciphertexts, multiple bodies, distinct LUTs, and amortized bootstrapping | strong prior-art risk for any claim that this project invents shared-mask multi-body TFHE batching |
| 2025/696 incomplete NTT | preliminary full text plus code metadata | public full-text page and GitHub repository describe incomplete-NTT amortized bootstrapping and reproducibility setup | adjacent acceleration baseline, not the same technique as PVW/MAT-SAB |
| TFHE/GSW background | background accessible | TFHE external-product and GSW/LWE background sources | only supports background/security boundaries; no novelty support |

## Refresh Update

A follow-up source refresh is recorded in
`docs/stage27_related_work_refresh_log.md` and
`repro/stage27_related_work_access_refresh.csv`.

Changes relative to the initial gate:

- `2025/686` remains partial: author metadata, repository metadata, and ACM
  metadata are usable, but full ePrint/ACM paper access is still blocked in
  this environment.
- `2025/2112` is now stronger novelty-risk evidence: public full-text and DBLP
  metadata are available for common-mask/shared-mask multi-body TFHE batching.
- `2025/696` incomplete-NTT amortized bootstrapping has accessible full ePrint
  PDF and code metadata; it is adjacent acceleration evidence, not the same
  PVW/MAT-SAB technique.
- GPVL23 and a 2026 bootstrapping survey are added only as background and
  positioning evidence.

## Citation Probe Update

The reproducible 2025/686 citation-access probe is recorded in
`docs/stage27_citation_gate_log.md` and
`repro/stage27_citation_access_probe/`.

Result:

```text
direct_pdf_access: BLOCKED
semantic_scholar_metadata: METADATA_AVAILABLE_NO_OPEN_ACCESS_PDF
dblp_title_metadata: TITLE_METADATA_AVAILABLE
citation_decision: BLOCK_THEOREM_LEVEL_CITATIONS
```

This confirms that metadata is enough for paper identity and code-lineage
context, but not enough for theorem, algorithm, remark, table, figure, or
experiment-number citations.

## Claim Boundary After This Gate

Allowed:

```text
Engineering/systems claim: this project integrates PVW/MAT shared-mask
multi-body batching into the tested binary 2025/686 SAB implementation and
shows complete-SAB throughput gains under the recorded backend and parameter
scope.
```

Blocked:

```text
Novel shared-mask batching claim.
Theoretical-optimal MAT-AVX512 claim.
Broad all-parameter or non-binary PVW-SAB claim.
Multi-fold SAB speedup claim.
```

## Remaining Work

- Obtain or manually inspect the full 2025/686 paper before citing precise
  theorem, algorithm, remark, or experiment numbers.
- Inspect the final publisher/ePrint version of 2025/2112 before writing a
  novelty distinction in manuscript language.
- Assemble the final performance/noise/resource manuscript package from the
  Stage 25, Stage 26, and Stage 27 matrices after the claim scope is fixed.
- If broad binary-parameter claims are desired, extend Stage 26 beyond the
  current 5-run/5-seed added-parameter evidence.

## Decision

Status:

```text
FULL_RELATED_WORK_GATE_STARTED
FAB686_FULL_TEXT_BLOCKED_IN_CURRENT_ENVIRONMENT
NOVELTY_CLAIM_STILL_BLOCKED
SAFE_ENGINEERING_CLAIM_REMAINS_AVAILABLE
RELATED_WORK_REFRESH_COMPLETED
CITATION_ACCESS_PROBE_COMPLETED
```
