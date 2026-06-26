# Stage95 Public Source Reprobe Plan

Date: 2026-06-26

## Objective

After Stage94 confirms no unblocked local hot-path candidate remains, reprobe
public 2025/686 source routes that may change over time and decide whether the
full-text and novelty blockers can move.

## Scope

Stage95 is an external-source evidence refresh. It does not modify SAB source
code, does not run benchmarks, and does not upgrade theorem-level or novelty
claims unless a reviewed full-text artifact becomes available.

## Inputs

- Stage94 local frontier audit.
- Stage72 external source refresh output after rerun.
- Stage91 claim boundary.
- Stage93 external lane attempt.

## Gates

- Stage94 must have passed.
- Stage72 current rerun must complete.
- Author metadata, DOI metadata, or code routes may be visible, but they must
  not be treated as theorem-level full text.
- Direct full-text routes must report `PDF_ACCESSIBLE` before CB7 can move.
- C3/C4/C5 stronger claims must remain blocked if direct full text is still
  unavailable.

## Expected Decision

```text
PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED
```

If a future rerun makes an official PDF accessible, rerun Stage38 with
`FAB686_FULLTEXT_PATH` after saving the artifact and hashing it.
