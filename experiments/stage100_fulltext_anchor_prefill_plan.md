# Stage100 Full-Text Anchor Prefill Plan

Date: 2026-06-26

## Goal

Use the Stage99/Stage38 registered 2025/686 PDF to generate candidate page
anchors for the six Stage38 manual review rows:

- protocol stages;
- complexity model;
- correctness/noise;
- parameter/security;
- PVW-SAB delta;
- novelty boundary.

## Method

Run `pdftotext` into a temporary file, split by page, search only predefined
technical keywords, and persist page/keyword metadata. Do not store extracted
paper text in the repro pack.

## Gates

- Stage99 decision must be
  `PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED`.
- `fab686_fulltext` must be `AVAILABLE_UNREVIEWED` and point to an existing
  PDF.
- Generated anchors must stay candidate-only and review-required.
- No theorem-level, novelty, or MAT-AVX512 optimality claim may be upgraded by
  this stage.

## Failure Policy

If no candidate pages are found for a row, keep that row review-required and
route it to manual PDF inspection. If `pdftotext` is unavailable, install a
local PDF text extractor or perform manual source-anchor review outside this
automated prefill.
