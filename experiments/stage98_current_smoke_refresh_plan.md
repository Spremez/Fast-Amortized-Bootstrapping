# Stage 98 Current-Head Smoke Refresh Plan

Date: 2026-06-26

## Goal

Refresh current-head smoke evidence after Stage97 without changing scalar SAB,
PVW/MAT-SAB, backend, or default build behavior. Stage98 is a continuity gate:
it proves that the current committed control-plane/source-guard work still
builds and runs the scalar default route and explicit PVW target routes.

## Tasks

- run the default scalar binary full program for `BINARY SET_2_3_2048`;
- run the explicit active-buffer PVW target full bootstrap gate;
- run the explicit H14 backend FromDFT-add PVW target full bootstrap gate;
- build the scalar ternary target to preserve non-binary scalar independence;
- aggregate raw build/run logs into a machine-checkable summary;
- keep Stage98 out of speedup, novelty, theorem-level, and hardware-counter
  claims.

## Gates

| gate | requirement |
|---|---|
| Stage97 precondition | Stage97 decision is `PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED` |
| scalar binary smoke | default scalar binary run ends with `Pass` |
| active PVW target smoke | explicit active-buffer PVW target gate prints `SAB_PVW target full bootstrap gate: Pass` |
| backend PVW target smoke | explicit H14 backend PVW target gate prints `SAB_PVW target full bootstrap gate: Pass` |
| scalar ternary build | scalar ternary build completes without enabling PVW |
| claim guard | Stage98 remains a current-head smoke refresh only |

## Failure Handling

- If scalar binary smoke fails, stop and debug scalar/default behavior before
  any PVW/MAT-SAB optimization work.
- If either PVW target gate fails, stop and inspect the explicit PVW path or
  build flags before claiming current-head continuity.
- If scalar ternary build fails, keep non-binary PVW claims unsupported and
  inspect scalar branch independence.
- If Stage97 precondition fails, refresh source-delta guards before interpreting
  smoke evidence.

## Expected Output

- `docs/stage98_current_smoke_refresh_log.md`
- `repro/stage98_current_smoke_refresh/summary.csv`
- `repro/stage98_current_smoke_refresh/raw_smoke.csv`
- `repro/stage98_current_smoke_refresh/artifact_index.csv`
- raw build/run logs under `repro/stage98_current_smoke_refresh/`
- `repro/stage98_current_smoke_refresh/stage98_run.log`
