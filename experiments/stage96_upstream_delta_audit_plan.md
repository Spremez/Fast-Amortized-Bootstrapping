# Stage96 Upstream Delta Audit Plan

Date: 2026-06-26

## Goal

Record the provenance boundary between the public `2025/686` implementation
route (`origin/main`) and the local PVW/MAT-SAB optimization chain.

Stage96 is not a new hot-path implementation and not a performance claim. It
answers a narrower reproducibility question: the public code route is visible,
the local branch is ahead of it, and the local PVW/MAT-SAB changes remain
explicitly auditable rather than silently redefining the scalar SAB baseline.

## Inputs

- `origin/main` after `git fetch origin`.
- `repro/stage95_public_source_reprobe/summary.csv`.
- `repro/stage91_final_package/claim_boundary.csv`.
- `src/mosfhet/Makefile.def`.
- `git diff --name-only origin/main..HEAD`.

## Gates

| gate | pass condition |
|---|---|
| Stage95 precondition | Stage95 decision is `PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED`. |
| upstream ref | `origin/main` resolves and is the merge-base of `HEAD` under the current fetch. |
| delta classification | local files changed since `origin/main` are classified by code/docs/repro/theory area. |
| default guard | PVW/MAT-SAB feature flags remain default-false in `src/mosfhet/Makefile.def`. |
| claim guard | Stage91 stronger claim boundaries remain blocked or missing-optional. |

## Outputs

- `docs/stage96_upstream_delta_audit_log.md`
- `repro/stage96_upstream_delta_audit/summary.csv`
- `repro/stage96_upstream_delta_audit/delta_by_area.csv`
- `repro/stage96_upstream_delta_audit/delta_files.csv`
- `repro/stage96_upstream_delta_audit/commit_range.csv`
- `repro/stage96_upstream_delta_audit/flag_guard.csv`
- `repro/stage96_upstream_delta_audit/artifact_index.csv`

## Failure Policy

If `origin/main` is missing, behind `HEAD`, or no longer the merge-base, do not
upgrade any upstream-provenance wording before inspecting the remote drift. If
any default flag changed to true, rerun current-head scalar/PVW smoke and
default-path guard checks before relying on the existing scalar baseline.
