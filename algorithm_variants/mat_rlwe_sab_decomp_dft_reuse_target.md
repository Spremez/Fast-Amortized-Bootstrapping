# V135: Decompose/DFT Reuse Target

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: generalized lane-pair input decompose/DFT.
- Optimization target: make closure-capable EP positive for r=4.
- Status labels: `[target-gate]`, `[not-rgsw]`, `[performance-blocker]`.
- Decision: `PASS_STAGE135_DECOMP_DFT_REUSE_TARGETS_READY_STAGE136`.

## Required Experiments

Stage136 must implement a decompose/DFT-targeted variant and compare it
against Stage134 for r=4 N=512/1024. RGSW integration remains rejected
until this kernel-level blocker is removed.
