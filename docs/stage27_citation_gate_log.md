# Stage 27 Citation Gate Log

Date: 2026-06-25

## Goal

Make the 2025/686 full-text citation gap reproducible. This gate checks whether
the project can support theorem-level, algorithm-level, remark-level, or
experiment-number citations to the base FAB paper from the current environment.

## Command

```sh
bash scripts/run_stage27_citation_access_probe.sh
```

## Probe Result

| source | status |
|---|---|
| ePrint landing page `https://eprint.iacr.org/2025/686` | `403` |
| ePrint PDF `https://eprint.iacr.org/2025/686.pdf` | `403` |
| ACM DOI landing page `https://dl.acm.org/doi/10.1145/3719027.3765181` | `403` |
| ACM PDF `https://dl.acm.org/doi/pdf/10.1145/3719027.3765181` | `403` |
| Semantic Scholar page | metadata/html only, no open-access PDF |
| Author page `https://antonioguimaraes.org/tag/amortized-bootstrapping/` | metadata/html only; title, abstract, ePrint, and code links |
| ResearchGate publication page | `403` |
| Semantic Scholar API | metadata available, `openAccessPdf.url` missing |
| DBLP title API | optional metadata route; may report title hits when DBLP responds |

Raw probe summaries:

- `repro/stage27_citation_access_probe/access_probe.csv`
- `repro/stage27_citation_access_probe/summary.csv`

## Decision

Status:

```text
FAB686_METADATA_AVAILABLE
FAB686_FULL_TEXT_NOT_AVAILABLE_IN_CURRENT_ENVIRONMENT
THEOREM_LEVEL_CITATIONS_BLOCKED
ENGINEERING_EVIDENCE_PACKAGE_REMAINS_VALID
```

Allowed:

```text
Use 2025/686 metadata for paper identity, abstract-level positioning, DOI,
authors, venue, and code lineage.
```

Blocked:

```text
Do not cite 2025/686 theorem, algorithm, remark, table, figure, or experiment
numbers until the full paper is manually provided and inspected.
```

This gate does not invalidate the local engineering evidence package. It only
prevents manuscript text from overclaiming support from an unavailable source.
