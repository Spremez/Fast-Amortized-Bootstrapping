# Stage99 External Blocker Reprobe Plan

Date: 2026-06-26

## Goal

After Stage98 current-head smoke continuity, reprobe the external blocker
state for final PVW/MAT-SAB claim upgrades. Stage99 does not change SAB code,
does not run a new full-SAB performance benchmark, and does not upgrade
speedup or novelty claims.

## Tasks

- verify Stage98 still reports `PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH`;
- rerun the lightweight Stage28 native perf-counter probe into a Stage99
  output directory;
- rerun the Stage27 citation/source access probe into a Stage99 output
  directory;
- search configured local roots for a plausible 2025/686 full-text artifact;
- summarize native-perf, full-text route, local full-text, novelty/source
  review, and claim-guard status;
- update the Stage19+ closure/repro pack so this external-blocker state is
  auditable.

## Gates

- Stage98 precondition must pass.
- Native perf is recorded as unlocked only when Stage28 reports usable
  hardware counters and, for final attribution, a correct benchmark run under
  perf.
- 2025/686 full text is recorded as reviewable only when a local PDF/text
  artifact is supplied or found; metadata, DOI, code, or HTML routes are not
  enough.
- Novelty remains blocked until manual full-text related-work/source-anchor
  review is completed.
- Stronger claims remain blocked unless the corresponding external gate is
  explicitly satisfied.

## Failure Handling

- If Stage98 is not passing, stop and refresh current-head smoke before any
  claim work.
- If `perf` is unavailable or blocked, keep CB5 as `WAIT_NATIVE_PERF`.
- If public routes expose metadata only or local search finds no artifact,
  keep CB7 as `WAIT_EXTERNAL_FULLTEXT`.
- If a full-text candidate is found, require Stage38 and manual review before
  changing final wording.
