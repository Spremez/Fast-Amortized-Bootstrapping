# Stage68 Frontier Closure Consistency Plan

## Goal

After Stage67, make the completion frontier agree with the closure/verifier
state. Specifically, Stage51 G6 must return to `LOCAL_READY` instead of
`LOCAL_REFRESH_PENDING`, and the Stage19+ control-plane label must be visible
across Stage42, Stage51, Stage57, and Stage59.

## Scope

This is a control-plane consistency stage. It does not change scalar SAB,
`sab_pvw_*`, MAT kernels, benchmark parameters, or measured speedup claims.

## Gate

- Stage42 `S42-OVERALL` must pass and still include the Stage67 integration
  evidence; the final post-Stage68 closure rebuild records the latest label.
- Stage51 `G6` must be `LOCAL_READY` and mention `Stage19-67`.
- Stage57 scope-label audit must pass with `latest_stage=67`.
- Stage59 current-head refresh route must mention Stage67 evidence.
- Stage68 decision must be `PASS_FRONTIER_CLOSURE_CONSISTENCY`.
