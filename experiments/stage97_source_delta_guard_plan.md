# Stage 97 Source Delta Guard Plan

Date: 2026-06-26

## Goal

Convert the post-Stage96 source-delta observation into a machine-checkable
guard for future PVW/MAT-SAB work. Stage97 does not implement a new hot-path
variant and does not run a new performance benchmark. It verifies that the
local source delta remains separated from the scalar/default SAB route before
the next optimization loop is allowed to claim continuity.

## Tasks

- reuse Stage96 upstream/local provenance as the precondition;
- inventory `origin/main..HEAD` source deltas under `main.c`, `include/`, and
  `src/`;
- prove scalar SAB implementation files do not reference PVW/MAT-SAB symbols;
- prove selected shared MOSFHET backend files do not reference `sab_pvw`
  symbols;
- verify PVW/MAT-SAB, AVX512, profile, and microbench flags remain
  default-false in `src/mosfhet/Makefile.def`;
- verify `pvwtmlwe.c` and `mattrgsw.c` are compiled only under
  `ENABLE_PVW_TMLWE=true`;
- bind the guard to the latest scalar/default smoke evidence from Stage33 and
  Stage89.

## Gates

| gate | requirement |
|---|---|
| Stage96 precondition | `stage96_decision` is `PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED` |
| source delta inventory | source/hot-path deltas are classified into scalar, shared backend, PVW/MAT-SAB, harness, and other buckets |
| scalar symbol guard | scalar SAB files contain no `SAB_PVW`, `sab_pvw`, `PVW_TMLWE`, or `MAT_TRGSW` tokens |
| shared backend guard | selected shared backend files contain no `SAB_PVW` or `sab_pvw` tokens |
| build flag guard | all tracked experimental flags remain `?= false`, and PVW/MAT sources are gated by `ENABLE_PVW_TMLWE` |
| smoke evidence guard | Stage33 and Stage89 scalar/default smoke summaries still pass |
| claim guard | Stage97 is recorded as source isolation evidence only, not as a speedup, novelty, or theorem claim |

## Failure Handling

- If scalar/default files contain PVW/MAT-SAB symbols, stop and inspect whether
  the scalar baseline was changed.
- If a build flag becomes default-true, rerun scalar/default correctness,
  performance, noise, and resource gates before relying on any continuity
  claim.
- If smoke evidence is missing or stale, rerun the current-smoke gate before
  continuing to hot-path work.
- If Stage96 provenance no longer passes, refresh upstream/local provenance
  before interpreting Stage97.

## Expected Output

- `docs/stage97_source_delta_guard_log.md`
- `repro/stage97_source_delta_guard/summary.csv`
- `repro/stage97_source_delta_guard/source_delta.csv`
- `repro/stage97_source_delta_guard/symbol_guard.csv`
- `repro/stage97_source_delta_guard/build_flag_guard.csv`
- `repro/stage97_source_delta_guard/smoke_evidence.csv`
- `repro/stage97_source_delta_guard/artifact_index.csv`
- `repro/stage97_source_delta_guard/stage97_run.log`
